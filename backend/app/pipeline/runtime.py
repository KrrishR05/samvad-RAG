"""
SAMVAD Pipeline Runtime Container

Wires Phase 2 persistence (DocumentStore), Lexical/Dense/Hybrid retrievers,
EmbeddingProvider, optional LLMGenerator, and PipelineOrchestrator together.
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Optional

from app.analytics.metrics import MetricsStore, get_metrics_store
from app.core.config import Settings, get_settings
from app.core.logging import get_logger
from app.embeddings.interfaces import EmbeddingProvider
from app.embeddings.providers import LocalTfidfSVDProvider, OpenAICompatibleEmbeddingProvider
from app.generation.generator import BaseLLMGenerator, create_generator_from_settings
from app.ingestion.chunker import chunk_text
from app.ingestion.loaders import load_document_bytes
from app.ingestion.store import DocumentRecord, DocumentStatus, DocumentStore
from app.pipeline.orchestrator import PipelineOrchestrator, set_orchestrator
from app.retrieval.dense import DenseRetriever
from app.retrieval.hybrid import HybridRetriever
from app.retrieval.lexical import LexicalRetriever
from app.schemas.pipeline import ChunkStrategy

logger = get_logger("pipeline.runtime")


def create_embedding_provider(settings: Settings) -> EmbeddingProvider:
    """Create the configured embedding provider (defaults to local TF-IDF+SVD baseline)."""
    provider = (settings.embedding_provider or "local_tfidf_svd").strip().lower()
    if provider in ("openai", "openai_compatible", "ollama") and settings.embedding_model:
        base_url = settings.embedding_base_url or (
            "http://localhost:11434/v1" if provider == "ollama" else "https://api.openai.com/v1"
        )
        return OpenAICompatibleEmbeddingProvider(
            model_name=settings.embedding_model,
            base_url=base_url,
            api_key=settings.llm_api_key,
            timeout_seconds=settings.stage_timeout_seconds,
        )
    return LocalTfidfSVDProvider(target_dimension=128)


class SamvadRuntime:
    """Owns live storage, index state, retrievers, generator, and orchestrator."""

    def __init__(
        self,
        *,
        settings: Optional[Settings] = None,
        metrics_store: Optional[MetricsStore] = None,
        generator: Optional[BaseLLMGenerator] = None,
        embedding_provider: Optional[EmbeddingProvider] = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.metrics_store = metrics_store or get_metrics_store()
        self.document_store = DocumentStore(Path(self.settings.sqlite_db_path))

        self.embedding_provider: EmbeddingProvider = (
            embedding_provider or create_embedding_provider(self.settings)
        )
        self.lexical_retriever = LexicalRetriever()
        self.dense_retriever = DenseRetriever(
            embedding_provider=self.embedding_provider,
            persist_dir=Path(self.settings.vector_db_path),
        )
        self.hybrid_retriever = HybridRetriever(
            dense_retriever=self.dense_retriever,
            lexical_retriever=self.lexical_retriever,
        )
        self.generator: Optional[BaseLLMGenerator] = (
            generator if generator is not None else create_generator_from_settings(self.settings)
        )

        self.orchestrator = PipelineOrchestrator(
            retrievers={
                "hybrid": self.hybrid_retriever,
                "dense": self.dense_retriever,
                "lexical": self.lexical_retriever,
            },
            default_retriever_key="hybrid",
            generator=self.generator,
            metrics_store=self.metrics_store,
            settings=self.settings,
        )
        self._index_lock = asyncio.Lock()

        # Restore lexical index & persisted dense vectors if available on disk
        existing_chunks = self.document_store.get_all_chunks()
        if existing_chunks:
            self.lexical_retriever.build_index(existing_chunks)
            self.dense_retriever.load_index()

    async def ensure_indexes_ready(self) -> None:
        """Rebuild in-memory/dense indexes if SQLite has chunks not yet indexed in dense."""
        chunks = self.document_store.get_all_chunks()
        dense_ok = await self.dense_retriever.health_check()
        if chunks and not dense_ok:
            await self.rebuild_indexes()

    async def rebuild_indexes(self) -> int:
        """Re-index all stored chunks into both Lexical and Dense retrievers."""
        async with self._index_lock:
            chunks = self.document_store.get_all_chunks()
            self.lexical_retriever.build_index(chunks)
            await self.dense_retriever.build_index(chunks)
            logger.info("Rebuilt lexical and dense indexes (%d chunks).", len(chunks))
            return len(chunks)

    async def ingest_document(
        self,
        *,
        filename: str,
        raw_bytes: bytes,
        language: Optional[str] = None,
        chunk_strategy: ChunkStrategy = ChunkStrategy.SLIDING_WINDOW,
        chunk_size: int = 800,
        chunk_overlap: int = 120,
    ) -> tuple[DocumentRecord, bool, int]:
        """
        Parse, deduplicate, chunk, persist, and index a document.

        Returns:
            (record, duplicate, total_chunks_indexed)
        """
        loaded = load_document_bytes(
            filename=filename,
            raw_bytes=raw_bytes,
            language=language,
            max_bytes=self.settings.max_document_upload_bytes,
        )
        record, created = self.document_store.register_document(
            filename=loaded.filename,
            content_hash=loaded.content_hash,
            media_type=loaded.media_type,
            language=loaded.language,
            metadata=loaded.metadata,
        )
        if not created:
            total = len(self.document_store.get_all_chunks())
            return record, True, total

        try:
            chunks = chunk_text(
                text=loaded.content,
                parent_document_id=record.doc_id,
                strategy=chunk_strategy,
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                language=loaded.language,
            )
            self.document_store.save_chunks(record.doc_id, chunks)
            total_indexed = await self.rebuild_indexes()
            self.document_store.update_status(record.doc_id, DocumentStatus.INDEXED)
            updated = self.document_store.get_document(record.doc_id)
            assert updated is not None
            return updated, False, total_indexed
        except Exception as exc:
            self.document_store.update_status(
                record.doc_id,
                DocumentStatus.FAILED,
                error_message=str(exc),
            )
            raise

    async def delete_document(self, doc_id: str) -> tuple[bool, int]:
        """Delete a document and rebuild active indexes."""
        deleted = self.document_store.delete_document(doc_id)
        if not deleted:
            return False, len(self.document_store.get_all_chunks())
        total_indexed = await self.rebuild_indexes()
        return True, total_indexed


_runtime: Optional[SamvadRuntime] = None


def get_runtime() -> SamvadRuntime:
    """Return the application-wide SamvadRuntime singleton."""
    global _runtime
    if _runtime is None:
        _runtime = SamvadRuntime()
    return _runtime


def set_runtime(runtime: Optional[SamvadRuntime]) -> None:
    """Override or clear the SamvadRuntime singleton (for testing)."""
    global _runtime
    _runtime = runtime
    set_orchestrator(runtime.orchestrator if runtime is not None else None)

