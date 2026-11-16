"""
SAMVAD Ingestion — SQLite Document & Chunk Provenance Store

Persists document lifecycle state (uploaded -> processed -> indexed | failed),
prevents duplicate ingestion via SHA-256 content hashes, and stores chunks
with full parent-document provenance.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Optional, Union

from pydantic import BaseModel, Field

from app.core.config import get_settings
from app.db.connection import DBConnectionWrapper, DatabaseManager, get_db
from app.db.schema import init_database_tables
from app.ingestion.chunker import DocumentChunk
from app.schemas.pipeline import ChunkMetadata, ChunkStrategy


class DocumentStatus(str, Enum):
    UPLOADED = "uploaded"
    PROCESSED = "processed"
    INDEXED = "indexed"
    FAILED = "failed"


class DocumentRecord(BaseModel):
    doc_id: str
    filename: str
    content_hash: str
    media_type: str
    language: Optional[str] = None
    status: DocumentStatus
    error_message: Optional[str] = None
    chunk_count: int = 0
    created_at: str
    updated_at: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class DocumentStore:
    """PostgreSQL and SQLite unified store for ingested documents and their chunks."""

    def __init__(
        self,
        db_path: Optional[Path] = None,
        db: Optional[DatabaseManager] = None,
    ) -> None:
        if db is not None:
            self.db = db
        elif db_path is not None and not get_settings().database_url:
            self.db = DatabaseManager(sqlite_db_path=db_path)
        else:
            self.db = get_db()
        self.db_path = self.db.sqlite_db_path
        self._init_schema()

    def _connect(self):
        return self.db.connection()

    def _init_schema(self) -> None:
        init_database_tables(self.db)

    @staticmethod
    def _now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()

    @staticmethod
    def _row_to_doc(row: Any) -> DocumentRecord:
        meta_val = row["metadata_json"]
        meta_dict = json.loads(meta_val) if isinstance(meta_val, str) else (meta_val or {})
        return DocumentRecord(
            doc_id=row["doc_id"],
            filename=row["filename"],
            content_hash=row["content_hash"],
            media_type=row["media_type"],
            language=row["language"],
            status=DocumentStatus(row["status"]),
            error_message=row["error_message"],
            chunk_count=row["chunk_count"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            metadata=meta_dict,
        )

    def get_by_hash(self, content_hash: str) -> Optional[DocumentRecord]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM documents WHERE content_hash = ?",
                (content_hash,),
            ).fetchone()
            return self._row_to_doc(row) if row else None

    def get_document(self, doc_id: str) -> Optional[DocumentRecord]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM documents WHERE doc_id = ?",
                (doc_id,),
            ).fetchone()
            return self._row_to_doc(row) if row else None

    def register_document(
        self,
        *,
        filename: str,
        content_hash: str,
        media_type: str,
        language: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None,
        doc_id: Optional[str] = None,
    ) -> tuple[DocumentRecord, bool]:
        """
        Register a document if its content_hash is new.

        Returns:
            (record, created) where created=False indicates an existing duplicate.
        """
        existing = self.get_by_hash(content_hash)
        if existing is not None:
            return existing, False

        now = self._now_iso()
        did = doc_id or f"doc-{uuid.uuid4().hex[:12]}"
        meta_json = json.dumps(metadata or {}, ensure_ascii=False)
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO documents (
                    doc_id, filename, content_hash, media_type, language,
                    status, error_message, chunk_count, created_at, updated_at, metadata_json
                ) VALUES (?, ?, ?, ?, ?, ?, NULL, 0, ?, ?, ?)
                """,
                (
                    did,
                    filename,
                    content_hash,
                    media_type,
                    language,
                    DocumentStatus.UPLOADED.value,
                    now,
                    now,
                    meta_json,
                ),
            )
        rec = self.get_document(did)
        assert rec is not None
        return rec, True

    def save_chunks(self, doc_id: str, chunks: list[DocumentChunk]) -> None:
        """Replace chunks for *doc_id* and mark document as PROCESSED."""
        now = self._now_iso()
        with self._connect() as conn:
            conn.execute("DELETE FROM chunks WHERE parent_document_id = ?", (doc_id,))
            conn.executemany(
                """
                INSERT INTO chunks (
                    chunk_id, parent_document_id, text, language, chunk_strategy,
                    chunk_index, total_chunks, char_count, token_count, extra_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        c.metadata.chunk_id,
                        doc_id,
                        c.text,
                        c.metadata.language,
                        c.metadata.chunk_strategy.value if c.metadata.chunk_strategy else None,
                        c.metadata.chunk_index,
                        c.metadata.total_chunks,
                        c.metadata.char_count,
                        c.metadata.token_count,
                        json.dumps(c.metadata.extra, ensure_ascii=False),
                    )
                    for c in chunks
                ],
            )
            conn.execute(
                """
                UPDATE documents
                SET status = ?, chunk_count = ?, error_message = NULL, updated_at = ?
                WHERE doc_id = ?
                """,
                (DocumentStatus.PROCESSED.value, len(chunks), now, doc_id),
            )

    def update_status(
        self,
        doc_id: str,
        status: DocumentStatus,
        error_message: Optional[str] = None,
    ) -> None:
        now = self._now_iso()
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE documents
                SET status = ?, error_message = ?, updated_at = ?
                WHERE doc_id = ?
                """,
                (status.value, error_message, now, doc_id),
            )

    def list_documents(self) -> list[DocumentRecord]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM documents ORDER BY created_at DESC"
            ).fetchall()
            return [self._row_to_doc(r) for r in rows]

    def get_all_chunks(self, language: Optional[str] = None) -> list[DocumentChunk]:
        with self._connect() as conn:
            if language:
                rows = conn.execute(
                    "SELECT * FROM chunks WHERE language = ? ORDER BY parent_document_id, chunk_index",
                    (language,),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM chunks ORDER BY parent_document_id, chunk_index"
                ).fetchall()

        results: list[DocumentChunk] = []
        for row in rows:
            try:
                strategy = (
                    ChunkStrategy(row["chunk_strategy"])
                    if row["chunk_strategy"]
                    else None
                )
            except (ValueError, KeyError):
                strategy = None
            extra_val = row["extra_json"]
            extra_dict = json.loads(extra_val) if isinstance(extra_val, str) else (extra_val or {})
            meta = ChunkMetadata(
                chunk_id=row["chunk_id"],
                parent_document_id=row["parent_document_id"],
                language=row["language"],
                chunk_strategy=strategy,
                chunk_index=row["chunk_index"],
                total_chunks=row["total_chunks"],
                char_count=row["char_count"],
                token_count=row["token_count"],
                extra=extra_dict,
            )
            results.append(DocumentChunk(text=row["text"], metadata=meta))
        return results

    def get_chunks_for_document(self, doc_id: str) -> list[DocumentChunk]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM chunks WHERE parent_document_id = ? ORDER BY chunk_index ASC",
                (doc_id,),
            ).fetchall()

        results: list[DocumentChunk] = []
        for row in rows:
            try:
                strategy = (
                    ChunkStrategy(row["chunk_strategy"])
                    if row["chunk_strategy"]
                    else None
                )
            except (ValueError, KeyError):
                strategy = None
            extra_val = row["extra_json"]
            extra_dict = json.loads(extra_val) if isinstance(extra_val, str) else (extra_val or {})
            meta = ChunkMetadata(
                chunk_id=row["chunk_id"],
                parent_document_id=row["parent_document_id"],
                language=row["language"],
                chunk_strategy=strategy,
                chunk_index=row["chunk_index"],
                total_chunks=row["total_chunks"],
                char_count=row["char_count"],
                token_count=row["token_count"],
                extra=extra_dict,
            )
            results.append(DocumentChunk(text=row["text"], metadata=meta))
        return results

    def delete_document(self, doc_id: str) -> bool:
        with self._connect() as conn:
            cur = conn.execute("DELETE FROM documents WHERE doc_id = ?", (doc_id,))
            return cur.rowcount > 0

