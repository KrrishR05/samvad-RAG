"""
SAMVAD Database Engine — Unified PostgreSQL & SQLite Manager

Provides seamless connection pooling, transaction management, and automatic
dialect translation between PostgreSQL (enterprise production) and SQLite
(local zero-dependency development).
"""

from __future__ import annotations

import logging
import re
import sqlite3
import threading
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Generator, Optional, Sequence, Union

logger = logging.getLogger("samvad.db")

try:
    import psycopg2
    import psycopg2.pool
    from psycopg2.extras import RealDictCursor
    HAS_PSYCOPG2 = True
except ImportError:
    HAS_PSYCOPG2 = False


class DBConnectionWrapper:
    """Wrapper that normalizes execute/commit/close between SQLite and psycopg2."""

    def __init__(self, raw_conn: Any, is_postgres: bool) -> None:
        self.raw_conn = raw_conn
        self.is_postgres = is_postgres
        self._active_cursor: Any = None

    def execute(self, sql: str, params: Optional[Sequence[Any]] = None) -> Any:
        if self.is_postgres:
            translated_sql = sql.replace("?", "%s")
            self._active_cursor = self.raw_conn.cursor(cursor_factory=RealDictCursor)
            self._active_cursor.execute(translated_sql, params or ())
            return self._active_cursor
        else:
            return self.raw_conn.execute(sql, params or ())

    def executemany(self, sql: str, seq_of_params: Sequence[Sequence[Any]]) -> Any:
        if self.is_postgres:
            translated_sql = sql.replace("?", "%s")
            self._active_cursor = self.raw_conn.cursor()
            self._active_cursor.executemany(translated_sql, seq_of_params)
            return self._active_cursor
        else:
            return self.raw_conn.executemany(sql, seq_of_params)

    def executescript(self, script: str) -> None:
        if self.is_postgres:
            with self.raw_conn.cursor() as cur:
                cur.execute(script)
        else:
            self.raw_conn.executescript(script)

    def commit(self) -> None:
        self.raw_conn.commit()

    def rollback(self) -> None:
        self.raw_conn.rollback()


class DatabaseManager:
    """
    Unified database manager supporting both PostgreSQL and SQLite.
    
    If `database_url` is provided (starts with 'postgres://' or 'postgresql://'),
    it configures a thread-safe PostgreSQL connection pool.
    Otherwise, it defaults to a local SQLite database file with WAL mode.
    """

    def __init__(
        self,
        database_url: Optional[str] = None,
        sqlite_db_path: Union[str, Path] = "./data/samvad.db",
    ) -> None:
        self.database_url = (database_url or "").strip()
        self.sqlite_db_path = Path(sqlite_db_path)
        self.is_postgres = bool(
            self.database_url.startswith("postgres://")
            or self.database_url.startswith("postgresql://")
        )

        self._pg_pool: Optional[psycopg2.pool.ThreadedConnectionPool] = None
        self._lock = threading.Lock()

        if self.is_postgres:
            if not HAS_PSYCOPG2:
                raise RuntimeError(
                    "PostgreSQL was requested (via DATABASE_URL), but psycopg2 is not installed. "
                    "Install psycopg2-binary in your Python environment."
                )
            self._init_pg_pool()
            logger.info("DatabaseManager initialized in PostgreSQL mode (Pooled).")
        else:
            self.sqlite_db_path.parent.mkdir(parents=True, exist_ok=True)
            logger.info(
                "DatabaseManager initialized in SQLite mode: %s",
                self.sqlite_db_path,
            )

    def _init_pg_pool(self) -> None:
        """Initialize PostgreSQL ThreadedConnectionPool."""
        # Convert modern postgresql+asyncpg:// or similar to standard postgresql://
        dsn = re.sub(r"^postgresql\+[a-zA-Z0-9_]+://", "postgresql://", self.database_url)
        # Handle 'postgres://' shorthand (common in Heroku / older setups)
        dsn = re.sub(r"^postgres://", "postgresql://", dsn)

        # For remote cloud databases like Supabase, ensure sslmode is specified
        if (
            "supabase.co" in dsn
            or "supabase.com" in dsn
            or "pooler.supabase.com" in dsn
        ) and "sslmode" not in dsn:
            sep = "&" if "?" in dsn else "?"
            dsn = f"{dsn}{sep}sslmode=require"

        try:
            self._pg_pool = psycopg2.pool.ThreadedConnectionPool(
                minconn=1,
                maxconn=20,
                dsn=dsn,
            )
            # Verify connectivity
            conn = self._pg_pool.getconn()
            try:
                with conn.cursor() as cur:
                    cur.execute("SELECT version();")
                    row = cur.fetchone()
                    logger.info("Connected to PostgreSQL: %s", row[0] if row else "OK")
            finally:
                self._pg_pool.putconn(conn)
        except Exception as exc:
            logger.error("Failed to connect to PostgreSQL with DATABASE_URL: %s", exc)
            raise

    def close(self) -> None:
        """Close connection pools on application shutdown."""
        if self._pg_pool is not None:
            self._pg_pool.closeall()
            self._pg_pool = None

    def _translate_sql(self, sql: str) -> str:
        """Translate SQL placeholders and dialect specifics."""
        if self.is_postgres:
            return sql.replace("?", "%s")
        return sql

    @contextmanager
    def connection(self) -> Generator[DBConnectionWrapper, None, None]:
        """Check out a database connection wrapped for uniform execution."""
        if self.is_postgres:
            assert self._pg_pool is not None, "PostgreSQL connection pool not initialized."
            conn = self._pg_pool.getconn()
            try:
                if getattr(conn, "closed", 0) != 0:
                    raise psycopg2.OperationalError("Closed connection")
                with conn.cursor() as probe_cur:
                    probe_cur.execute("SELECT 1;")
            except Exception:
                try:
                    self._pg_pool.putconn(conn, close=True)
                except Exception:
                    pass
                conn = self._pg_pool.getconn()

            wrapper = DBConnectionWrapper(conn, is_postgres=True)
            try:
                yield wrapper
                if getattr(conn, "closed", 0) == 0:
                    wrapper.commit()
            except Exception:
                if getattr(conn, "closed", 0) == 0:
                    try:
                        wrapper.rollback()
                    except Exception:
                        pass
                raise
            finally:
                try:
                    if getattr(conn, "closed", 0) != 0:
                        self._pg_pool.putconn(conn, close=True)
                    else:
                        self._pg_pool.putconn(conn)
                except Exception:
                    pass
        else:
            conn = sqlite3.connect(str(self.sqlite_db_path), timeout=30.0)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA foreign_keys = ON;")
            conn.execute("PRAGMA journal_mode = WAL;")
            wrapper = DBConnectionWrapper(conn, is_postgres=False)
            try:
                yield wrapper
                wrapper.commit()
            except Exception:
                wrapper.rollback()
                raise
            finally:
                conn.close()

    def execute(self, sql: str, params: Optional[Sequence[Any]] = None) -> int:
        """Execute a write statement (INSERT, UPDATE, DELETE) and commit."""
        with self.connection() as conn:
            cur = conn.execute(sql, params)
            conn.commit()
            return getattr(cur, "rowcount", 0)

    def execute_many(self, sql: str, seq_of_params: Sequence[Sequence[Any]]) -> int:
        """Execute batch writes with parameters."""
        with self.connection() as conn:
            cur = conn.executemany(sql, seq_of_params)
            conn.commit()
            return getattr(cur, "rowcount", 0)

    def fetch_one(self, sql: str, params: Optional[Sequence[Any]] = None) -> Optional[dict[str, Any]]:
        """Execute a SELECT query and return a single row as a dict or None."""
        with self.connection() as conn:
            cur = conn.execute(sql, params)
            row = cur.fetchone()
            return dict(row) if row is not None else None

    def fetch_all(self, sql: str, params: Optional[Sequence[Any]] = None) -> list[dict[str, Any]]:
        """Execute a SELECT query and return all matching rows as a list of dicts."""
        with self.connection() as conn:
            cur = conn.execute(sql, params)
            rows = cur.fetchall()
            return [dict(r) for r in rows]

    def execute_script(self, script: str) -> None:
        """Execute multi-statement DDL scripts (e.g. table creations)."""
        with self.connection() as conn:
            conn.executescript(script)
            conn.commit()


# Global Singleton
_db_manager: Optional[DatabaseManager] = None
_db_lock = threading.Lock()


def get_db() -> DatabaseManager:
    """Return the global DatabaseManager singleton instance."""
    global _db_manager
    if _db_manager is None:
        with _db_lock:
            if _db_manager is None:
                from app.core.config import get_settings
                settings = get_settings()
                _db_manager = DatabaseManager(
                    database_url=getattr(settings, "database_url", None),
                    sqlite_db_path=getattr(settings, "sqlite_db_path", "./data/samvad.db"),
                )
    return _db_manager


def reset_db_singleton() -> None:
    """Reset singleton instance (useful in test harnesses)."""
    global _db_manager
    with _db_lock:
        if _db_manager is not None:
            _db_manager.close()
            _db_manager = None
