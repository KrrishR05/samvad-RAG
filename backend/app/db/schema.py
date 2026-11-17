"""
SAMVAD Database Schema Definitions

Creates and verifies unified tables for both PostgreSQL and SQLite.
"""

from __future__ import annotations

import logging
from app.db.connection import DatabaseManager

logger = logging.getLogger("samvad.db.schema")

_SCHEMA_INITIALIZED = False


def init_database_tables(db: DatabaseManager, force: bool = False) -> None:
    """Initialize all core application tables and indexes once."""
    global _SCHEMA_INITIALIZED
    if _SCHEMA_INITIALIZED and not force:
        return
    _SCHEMA_INITIALIZED = True

    logger.info("Initializing SAMVAD database schema (PostgreSQL=%s)...", db.is_postgres)

    # Optional PostgreSQL extensions
    if db.is_postgres:
        try:
            db.execute("CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";")
        except Exception as e:
            logger.debug("uuid-ossp extension skipped: %s", e)
        try:
            db.execute("CREATE SCHEMA IF NOT EXISTS extensions;")
            db.execute("CREATE EXTENSION IF NOT EXISTS vector WITH SCHEMA extensions;")
            logger.info("pgvector extension verified on PostgreSQL.")
        except Exception as e:
            logger.debug("pgvector extension not installed or permission restricted: %s", e)

    # 1. Documents & Chunks
    db.execute_script(
        """
        CREATE TABLE IF NOT EXISTS documents (
            doc_id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL DEFAULT 'usr_krrish_default',
            filename TEXT NOT NULL,
            content_hash TEXT NOT NULL,
            media_type TEXT NOT NULL,
            language TEXT,
            status TEXT NOT NULL,
            error_message TEXT,
            chunk_count INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            metadata_json TEXT NOT NULL DEFAULT '{}'
        );

        CREATE TABLE IF NOT EXISTS chunks (
            chunk_id TEXT PRIMARY KEY,
            user_id TEXT DEFAULT 'usr_krrish_default',
            parent_document_id TEXT NOT NULL,
            text TEXT NOT NULL,
            language TEXT,
            chunk_strategy TEXT,
            chunk_index INTEGER,
            total_chunks INTEGER,
            char_count INTEGER,
            token_count INTEGER,
            extra_json TEXT NOT NULL DEFAULT '{}',
            FOREIGN KEY (parent_document_id) REFERENCES documents(doc_id) ON DELETE CASCADE
        );

        CREATE INDEX IF NOT EXISTS idx_chunks_parent ON chunks(parent_document_id);
        """
    )

    # Migrate existing documents and chunks tables to include user_id if not present
    if db.is_postgres:
        try:
            db.execute("ALTER TABLE public.documents ADD COLUMN IF NOT EXISTS user_id TEXT NOT NULL DEFAULT 'usr_krrish_default';")
            db.execute("ALTER TABLE public.chunks ADD COLUMN IF NOT EXISTS user_id TEXT DEFAULT 'usr_krrish_default';")
            db.execute("CREATE INDEX IF NOT EXISTS idx_documents_user ON public.documents(user_id);")
            db.execute("CREATE INDEX IF NOT EXISTS idx_chunks_user ON public.chunks(user_id);")
        except Exception as exc:
            logger.debug("PostgreSQL column user_id check: %s", exc)
    else:
        try:
            # SQLite safe column addition
            doc_cols = [r["name"] for r in db.fetch_all("PRAGMA table_info(documents);")]
            if "user_id" not in doc_cols:
                db.execute("ALTER TABLE documents ADD COLUMN user_id TEXT NOT NULL DEFAULT 'usr_krrish_default';")
            chunk_cols = [r["name"] for r in db.fetch_all("PRAGMA table_info(chunks);")]
            if "user_id" not in chunk_cols:
                db.execute("ALTER TABLE chunks ADD COLUMN user_id TEXT DEFAULT 'usr_krrish_default';")
            db.execute("CREATE INDEX IF NOT EXISTS idx_documents_user ON documents(user_id);")
            db.execute("CREATE INDEX IF NOT EXISTS idx_chunks_user ON chunks(user_id);")
        except Exception as exc:
            logger.debug("SQLite column user_id check: %s", exc)

    # 2. Authentication & Users
    db.execute_script(
        """
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            email TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            password_hash TEXT,
            salt TEXT,
            provider TEXT NOT NULL DEFAULT 'email',
            google_id TEXT,
            avatar_url TEXT,
            plan TEXT NOT NULL DEFAULT 'free',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
        CREATE INDEX IF NOT EXISTS idx_users_google_id ON users(google_id);

        CREATE TABLE IF NOT EXISTS sessions (
            token TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            created_at TEXT NOT NULL,
            expires_at TEXT NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
        );

        CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id);

        CREATE TABLE IF NOT EXISTS pro_waitlist (
            id TEXT PRIMARY KEY,
            email TEXT UNIQUE NOT NULL,
            name TEXT,
            user_id TEXT,
            created_at TEXT NOT NULL,
            notified INTEGER DEFAULT 0
        );
        """
    )

    # 3. Analytics & Telemetry Traces
    db.execute_script(
        """
        CREATE TABLE IF NOT EXISTS analytics_records (
            request_id TEXT PRIMARY KEY,
            query_id TEXT,
            timestamp TEXT NOT NULL,
            success INTEGER DEFAULT 1,
            strategy TEXT,
            query_text TEXT,
            chunks_retrieved INTEGER,
            cached INTEGER DEFAULT 0,
            stt_ms REAL,
            query_processing_ms REAL,
            embedding_ms REAL,
            retrieval_ms REAL,
            reranking_ms REAL,
            generation_ms REAL,
            guardrail_ms REAL,
            total_ms REAL
        );

        CREATE INDEX IF NOT EXISTS idx_analytics_timestamp ON analytics_records(timestamp);
        """
    )

    # Enable Row Level Security (RLS) on PostgreSQL for enterprise data isolation
    if db.is_postgres:
        for table_name in ["documents", "chunks", "users", "sessions", "pro_waitlist", "analytics_records"]:
            try:
                db.execute(f"ALTER TABLE public.{table_name} ENABLE ROW LEVEL SECURITY;")
            except Exception as exc:
                logger.debug("Enable RLS on %s: %s", table_name, exc)

    logger.info("SAMVAD database schema initialized successfully.")

