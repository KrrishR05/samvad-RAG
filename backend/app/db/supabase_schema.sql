-- ═══════════════════════════════════════════════════════════════════════════════
-- SAMVAD — Supabase PostgreSQL Schema & Extensions
-- Run this script in your Supabase SQL Editor (or let SAMVAD auto-run it on startup)
-- ═══════════════════════════════════════════════════════════════════════════════

-- 1. Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS vector;

-- 2. Documents table (Knowledge Base metadata & provenance)
CREATE TABLE IF NOT EXISTS documents (
    doc_id TEXT PRIMARY KEY,
    filename TEXT NOT NULL,
    content_hash TEXT NOT NULL UNIQUE,
    media_type TEXT NOT NULL,
    language TEXT,
    status TEXT NOT NULL DEFAULT 'indexed',
    error_message TEXT,
    chunk_count INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    metadata_json TEXT NOT NULL DEFAULT '{}'
);

-- 3. Document Chunks table (stores text passages, token counts, and vector embeddings)
CREATE TABLE IF NOT EXISTS chunks (
    chunk_id TEXT PRIMARY KEY,
    parent_document_id TEXT NOT NULL REFERENCES documents(doc_id) ON DELETE CASCADE,
    text TEXT NOT NULL,
    language TEXT,
    chunk_strategy TEXT,
    chunk_index INTEGER,
    total_chunks INTEGER,
    char_count INTEGER,
    token_count INTEGER,
    extra_json TEXT NOT NULL DEFAULT '{}',
    embedding vector(384) -- Optional: for dense pgvector cosine search (e.g. all-MiniLM-L6-v2)
);

CREATE INDEX IF NOT EXISTS idx_chunks_parent ON chunks(parent_document_id);
CREATE INDEX IF NOT EXISTS idx_chunks_lang ON chunks(language);

-- 4. Users table (Authentication & User Profile)
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
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_google_id ON users(google_id);

-- 5. User Sessions table
CREATE TABLE IF NOT EXISTS sessions (
    token TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMPTZ NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id);

-- 6. Pro Waitlist table
CREATE TABLE IF NOT EXISTS pro_waitlist (
    id TEXT PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    name TEXT,
    user_id TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    notified INTEGER DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_waitlist_email ON pro_waitlist(email);

-- 7. Analytics & Request Telemetry Records
CREATE TABLE IF NOT EXISTS analytics_records (
    request_id TEXT PRIMARY KEY,
    query_id TEXT,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
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

-- 8. Enable Row Level Security (RLS) on all tables
-- This secures all tables against anonymous browser requests via Supabase public REST API,
-- while allowing the SAMVAD backend (connected as postgres service role) full access.
ALTER TABLE public.documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.chunks ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.pro_waitlist ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.analytics_records ENABLE ROW LEVEL SECURITY;


