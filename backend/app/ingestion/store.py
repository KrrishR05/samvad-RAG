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
    user_id: str = "usr_krrish_default"
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
        uid = (
            row.get("user_id")
            if isinstance(row, dict)
            else (getattr(row, "user_id", None) or "usr_krrish_default")
        ) or "usr_krrish_default"
        return DocumentRecord(
            doc_id=row["doc_id"],
            user_id=uid,
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

    def get_by_hash(
        self, content_hash: str, user_id: Optional[str] = None
    ) -> Optional[DocumentRecord]:
        with self._connect() as conn:
            if user_id:
                row = conn.execute(
                    "SELECT * FROM documents WHERE content_hash = ? AND user_id = ?",
                    (content_hash, user_id),
                ).fetchone()
            else:
                row = conn.execute(
                    "SELECT * FROM documents WHERE content_hash = ?",
                    (content_hash,),
                ).fetchone()
            return self._row_to_doc(row) if row else None

    def get_document(
        self, doc_id: str, user_id: Optional[str] = None
    ) -> Optional[DocumentRecord]:
        with self._connect() as conn:
            if user_id:
                row = conn.execute(
                    "SELECT * FROM documents WHERE doc_id = ? AND user_id = ?",
                    (doc_id, user_id),
                ).fetchone()
            else:
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
        user_id: str = "usr_krrish_default",
    ) -> tuple[DocumentRecord, bool]:
        """
        Register a document if its content_hash is new for this user.

        Returns:
            (record, created) where created=False indicates an existing duplicate for this user.
        """
        existing = self.get_by_hash(content_hash, user_id=user_id)
        if existing is not None:
            return existing, False

        now = self._now_iso()
        did = doc_id or f"doc-{uuid.uuid4().hex[:12]}"
        meta_json = json.dumps(metadata or {}, ensure_ascii=False)
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO documents (
                    doc_id, user_id, filename, content_hash, media_type, language,
                    status, error_message, chunk_count, created_at, updated_at, metadata_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, NULL, 0, ?, ?, ?)
                """,
                (
                    did,
                    user_id,
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
        rec = self.get_document(did, user_id=user_id)
        assert rec is not None
        return rec, True

    def save_chunks(
        self,
        doc_id: str,
        chunks: list[DocumentChunk],
        user_id: Optional[str] = None,
    ) -> None:
        """Replace chunks for *doc_id* and mark document as PROCESSED."""
        now = self._now_iso()
        # Resolve user_id if not explicitly provided
        uid = user_id
        if not uid:
            doc = self.get_document(doc_id)
            uid = doc.user_id if doc else "usr_krrish_default"

        with self._connect() as conn:
            conn.execute("DELETE FROM chunks WHERE parent_document_id = ?", (doc_id,))
            conn.executemany(
                """
                INSERT INTO chunks (
                    chunk_id, user_id, parent_document_id, text, language, chunk_strategy,
                    chunk_index, total_chunks, char_count, token_count, extra_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        c.metadata.chunk_id,
                        uid,
                        doc_id,
                        c.text,
                        c.metadata.language,
                        c.metadata.chunk_strategy.value if c.metadata.chunk_strategy else None,
                        c.metadata.chunk_index,
                        c.metadata.total_chunks,
                        c.metadata.char_count,
                        c.metadata.token_count,
                        json.dumps({**(c.metadata.extra or {}), "user_id": uid}, ensure_ascii=False),
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

    def list_documents(self, user_id: Optional[str] = None) -> list[DocumentRecord]:
        with self._connect() as conn:
            if user_id:
                rows = conn.execute(
                    "SELECT * FROM documents WHERE user_id = ? ORDER BY created_at DESC",
                    (user_id,),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM documents ORDER BY created_at DESC"
                ).fetchall()
            return [self._row_to_doc(r) for r in rows]

    def get_all_chunks(
        self, language: Optional[str] = None, user_id: Optional[str] = None
    ) -> list[DocumentChunk]:
        with self._connect() as conn:
            params: list[Any] = []
            clauses: list[str] = []
            if language:
                clauses.append("language = ?")
                params.append(language)
            if user_id:
                clauses.append("user_id = ?")
                params.append(user_id)

            where_str = f"WHERE {' AND '.join(clauses)}" if clauses else ""
            sql = f"SELECT * FROM chunks {where_str} ORDER BY parent_document_id, chunk_index"
            rows = conn.execute(sql, tuple(params)).fetchall()

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
            row_dict = dict(row) if hasattr(row, "keys") else (row if isinstance(row, dict) else {})
            uid_val = row_dict.get("user_id")
            if "user_id" not in extra_dict and uid_val:
                extra_dict["user_id"] = uid_val
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

    def get_chunks_for_document(
        self, doc_id: str, user_id: Optional[str] = None
    ) -> list[DocumentChunk]:
        with self._connect() as conn:
            if user_id:
                # Validate ownership
                owner_check = conn.execute(
                    "SELECT doc_id FROM documents WHERE doc_id = ? AND user_id = ?",
                    (doc_id, user_id),
                ).fetchone()
                if not owner_check:
                    return []

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
            row_dict = dict(row) if hasattr(row, "keys") else (row if isinstance(row, dict) else {})
            uid_val = row_dict.get("user_id")
            if "user_id" not in extra_dict and uid_val:
                extra_dict["user_id"] = uid_val
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

    def delete_document(self, doc_id: str, user_id: Optional[str] = None) -> bool:
        with self._connect() as conn:
            if user_id:
                cur = conn.execute(
                    "DELETE FROM documents WHERE doc_id = ? AND user_id = ?",
                    (doc_id, user_id),
                )
            else:
                cur = conn.execute("DELETE FROM documents WHERE doc_id = ?", (doc_id,))
            return cur.rowcount > 0

