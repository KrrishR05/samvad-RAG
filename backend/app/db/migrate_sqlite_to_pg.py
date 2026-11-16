"""
SAMVAD Data Migration Utility — SQLite to PostgreSQL

Migrates all indexed documents, chunks, users, sessions, and waitlist records
from local SQLite (data/samvad.db) to PostgreSQL with zero data loss and
full idempotency (ON CONFLICT DO NOTHING).

Usage:
    python -m app.db.migrate_sqlite_to_pg
    python -m app.db.migrate_sqlite_to_pg --pg-url "postgresql://user:pass@localhost:5432/samvad"
"""

from __future__ import annotations

import argparse
import logging
import sqlite3
import sys
from pathlib import Path
from typing import Any

from app.core.config import get_settings
from app.db.connection import DatabaseManager
from app.db.schema import init_database_tables

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)-7s | %(message)s")
logger = logging.getLogger("samvad.db.migrate")


def migrate_sqlite_to_postgres(
    sqlite_path: Path,
    pg_url: str,
) -> dict[str, int]:
    """Migrate all data from SQLite to PostgreSQL."""
    if not sqlite_path.exists():
        logger.warning("Source SQLite database not found at %s. Nothing to migrate.", sqlite_path)
        return {}

    logger.info("Starting migration from SQLite [%s] -> PostgreSQL...", sqlite_path)
    
    # 1. Connect to PostgreSQL and ensure tables exist
    pg_db = DatabaseManager(database_url=pg_url)
    if not pg_db.is_postgres:
        raise ValueError(f"Target URL is not a valid PostgreSQL URL: {pg_url}")

    init_database_tables(pg_db)

    # 2. Connect to SQLite
    sqlite_conn = sqlite3.connect(str(sqlite_path))
    sqlite_conn.row_factory = sqlite3.Row

    stats: dict[str, int] = {
        "users": 0,
        "sessions": 0,
        "pro_waitlist": 0,
        "documents": 0,
        "chunks": 0,
        "analytics_records": 0,
    }

    # Helper to check if a table exists in SQLite
    def table_exists(table_name: str) -> bool:
        cur = sqlite_conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (table_name,),
        )
        return cur.fetchone() is not None

    # A. Migrate users
    if table_exists("users"):
        rows = sqlite_conn.execute("SELECT * FROM users").fetchall()
        for r in rows:
            pg_db.execute(
                """
                INSERT INTO users (id, email, name, password_hash, salt, provider, google_id, avatar_url, plan, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO NOTHING;
                """,
                (
                    r["id"], r["email"], r["name"], r["password_hash"], r["salt"],
                    r["provider"], r["google_id"], r["avatar_url"], r["plan"],
                    r["created_at"], r["updated_at"],
                ),
            )
            stats["users"] += 1
        logger.info("Migrated %d users.", stats["users"])

    # B. Migrate sessions
    if table_exists("sessions"):
        rows = sqlite_conn.execute("SELECT * FROM sessions").fetchall()
        for r in rows:
            pg_db.execute(
                """
                INSERT INTO sessions (token, user_id, created_at, expires_at)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (token) DO NOTHING;
                """,
                (r["token"], r["user_id"], r["created_at"], r["expires_at"]),
            )
            stats["sessions"] += 1
        logger.info("Migrated %d sessions.", stats["sessions"])

    # C. Migrate pro_waitlist
    if table_exists("pro_waitlist"):
        rows = sqlite_conn.execute("SELECT * FROM pro_waitlist").fetchall()
        for r in rows:
            pg_db.execute(
                """
                INSERT INTO pro_waitlist (id, email, name, user_id, created_at, notified)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO NOTHING;
                """,
                (r["id"], r["email"], r["name"], r["user_id"], r["created_at"], r["notified"]),
            )
            stats["pro_waitlist"] += 1
        logger.info("Migrated %d pro waitlist subscriptions.", stats["pro_waitlist"])

    # D. Migrate documents
    if table_exists("documents"):
        rows = sqlite_conn.execute("SELECT * FROM documents").fetchall()
        for r in rows:
            pg_db.execute(
                """
                INSERT INTO documents (
                    doc_id, filename, content_hash, media_type, language,
                    status, error_message, chunk_count, created_at, updated_at, metadata_json
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (doc_id) DO NOTHING;
                """,
                (
                    r["doc_id"], r["filename"], r["content_hash"], r["media_type"],
                    r["language"], r["status"], r["error_message"], r["chunk_count"],
                    r["created_at"], r["updated_at"], r["metadata_json"],
                ),
            )
            stats["documents"] += 1
        logger.info("Migrated %d documents.", stats["documents"])

    # E. Migrate chunks
    if table_exists("chunks"):
        rows = sqlite_conn.execute("SELECT * FROM chunks").fetchall()
        batch_size = 200
        batch: list[tuple[Any, ...]] = []
        for r in rows:
            batch.append((
                r["chunk_id"], r["parent_document_id"], r["text"], r["language"],
                r["chunk_strategy"], r["chunk_index"], r["total_chunks"],
                r["char_count"], r["token_count"], r["extra_json"],
            ))
            if len(batch) >= batch_size:
                pg_db.execute_many(
                    """
                    INSERT INTO chunks (
                        chunk_id, parent_document_id, text, language, chunk_strategy,
                        chunk_index, total_chunks, char_count, token_count, extra_json
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (chunk_id) DO NOTHING;
                    """,
                    batch,
                )
                stats["chunks"] += len(batch)
                batch = []

        if batch:
            pg_db.execute_many(
                """
                INSERT INTO chunks (
                    chunk_id, parent_document_id, text, language, chunk_strategy,
                    chunk_index, total_chunks, char_count, token_count, extra_json
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (chunk_id) DO NOTHING;
                """,
                batch,
            )
            stats["chunks"] += len(batch)
        logger.info("Migrated %d chunks.", stats["chunks"])

    # F. Migrate analytics_records
    if table_exists("analytics_records"):
        rows = sqlite_conn.execute("SELECT * FROM analytics_records").fetchall()
        for r in rows:
            pg_db.execute(
                """
                INSERT INTO analytics_records (
                    request_id, query_id, timestamp, success, strategy,
                    query_text, chunks_retrieved, cached, stt_ms,
                    query_processing_ms, embedding_ms, retrieval_ms,
                    reranking_ms, generation_ms, guardrail_ms, total_ms
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (request_id) DO NOTHING;
                """,
                (
                    r["request_id"], r["query_id"], r["timestamp"], r["success"], r["strategy"],
                    r["query_text"], r["chunks_retrieved"], r["cached"], r["stt_ms"],
                    r["query_processing_ms"], r["embedding_ms"], r["retrieval_ms"],
                    r["reranking_ms"], r["generation_ms"], r["guardrail_ms"], r["total_ms"],
                ),
            )
            stats["analytics_records"] += 1
        logger.info("Migrated %d analytics traces.", stats["analytics_records"])

    sqlite_conn.close()
    pg_db.close()

    logger.info("✅ Migration completed successfully! Summary: %s", stats)
    return stats


def main() -> None:
    parser = argparse.ArgumentParser(description="Migrate SAMVAD data from SQLite to PostgreSQL")
    parser.add_argument(
        "--sqlite-path",
        default="./data/samvad.db",
        help="Path to source SQLite file (default: ./data/samvad.db)",
    )
    parser.add_argument(
        "--pg-url",
        default=None,
        help="Target PostgreSQL connection URL (e.g. postgresql://user:pass@localhost:5432/samvad). Defaults to DATABASE_URL in .env",
    )
    args = parser.parse_args()

    settings = get_settings()
    target_url = args.pg_url or getattr(settings, "database_url", None)

    if not target_url:
        logger.error(
            "No PostgreSQL URL provided! Specify --pg-url or set DATABASE_URL in backend/.env"
        )
        sys.exit(1)

    migrate_sqlite_to_postgres(Path(args.sqlite_path), target_url)


if __name__ == "__main__":
    main()

