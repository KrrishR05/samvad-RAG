"""
SAMVAD Retrieval — Dense

Vector similarity retriever backed by an EmbeddingProvider and L2-normalized
cosine search (with optional on-disk persistence under `vector_db_path`).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional, Sequence

import numpy as np

from app.core.errors import RetrievalError
from app.embeddings.interfaces import EmbeddingProvider
from app.embeddings.providers import LocalTfidfSVDProvider
from app.ingestion.chunker import DocumentChunk
from app.pipeline.interfaces import ScoredChunk
from app.schemas.pipeline import ChunkMetadata


def _l2_normalize_vec(vec: np.ndarray) -> np.ndarray:
    norm = float(np.linalg.norm(vec))
    if norm == 0.0:
        return vec.astype(np.float32)
    return (vec / norm).astype(np.float32)


class DenseRetriever:
    """Dense cosine-similarity retriever implementing the canonical Retriever protocol."""

    strategy_name = "dense"

    def __init__(
        self,
        embedding_provider: Optional[EmbeddingProvider] = None,
        *,
        persist_dir: Optional[Path | str] = None,
        min_score: float = 0.0,
    ) -> None:
        self.embedding_provider: EmbeddingProvider = (
            embedding_provider or LocalTfidfSVDProvider()
        )
        self.persist_dir: Optional[Path] = Path(persist_dir) if persist_dir else None
        self.min_score = min_score
        self._chunks: list[DocumentChunk] = []
        self._vectors: Optional[np.ndarray] = None

    async def build_index(self, chunks: Sequence[DocumentChunk]) -> None:
        """Embed *chunks*, store normalized vectors in memory, and persist if configured."""
        self._chunks = list(chunks)
        if not self._chunks:
            self._vectors = None
            if self.persist_dir:
                self._clear_persisted()
            return

        texts = [chunk.text for chunk in self._chunks]
        fit_fn = getattr(self.embedding_provider, "fit", None)
        if callable(fit_fn):
            fit_fn(texts)

        vectors = await self.embedding_provider.embed_documents(texts)
        if vectors.ndim != 2 or vectors.shape[0] != len(self._chunks):
            raise RetrievalError("Dense index build produced mismatched vector dimensions.")
        self._vectors = vectors.astype(np.float32)

        if self.persist_dir:
            self._save_persisted()

    def load_index(self) -> bool:
        """
        Restore vectors and chunk metadata from `persist_dir` if present.

        Returns True if an index was loaded, False otherwise.
        """
        if not self.persist_dir:
            return False
        vectors_path = self.persist_dir / "vectors.npz"
        chunks_path = self.persist_dir / "chunks.json"
        if not vectors_path.exists() or not chunks_path.exists():
            return False

        raw_chunks = json.loads(chunks_path.read_text(encoding="utf-8"))
        self._chunks = [
            DocumentChunk(
                text=item["text"],
                metadata=ChunkMetadata.model_validate(item["metadata"]),
            )
            for item in raw_chunks
        ]
        with np.load(vectors_path) as data:
            self._vectors = data["vectors"].astype(np.float32)

        # Deterministic local TF-IDF/SVD providers need vocabulary fitted to embed queries.
        fit_fn = getattr(self.embedding_provider, "fit", None)
        if callable(fit_fn) and self._chunks:
            fit_fn([chunk.text for chunk in self._chunks])

        return len(self._chunks) > 0 and self._vectors is not None

    def _save_persisted(self) -> None:
        if not self.persist_dir or self._vectors is None:
            return
        self.persist_dir.mkdir(parents=True, exist_ok=True)
        np.savez_compressed(self.persist_dir / "vectors.npz", vectors=self._vectors)
        serialized = [
            {"text": chunk.text, "metadata": chunk.metadata.model_dump(mode="json")}
            for chunk in self._chunks
        ]
        (self.persist_dir / "chunks.json").write_text(
            json.dumps(serialized, ensure_ascii=False),
            encoding="utf-8",
        )

    def _clear_persisted(self) -> None:
        if not self.persist_dir:
            return
        for filename in ("vectors.npz", "chunks.json"):
            target = self.persist_dir / filename
            if target.exists():
                target.unlink()

    async def retrieve(
        self,
        query: str,
        top_k: int = 10,
        language: Optional[str] = None,
    ) -> Sequence[ScoredChunk]:
        """Return top-k chunks ranked by cosine similarity against *query*."""
        if top_k <= 0:
            raise ValueError("top_k must be positive.")
        if not query or not query.strip() or not self._chunks or self._vectors is None:
            return []

        query_vec = _l2_normalize_vec(await self.embedding_provider.embed_query(query))
        if query_vec.shape[0] != self._vectors.shape[1]:
            raise RetrievalError(
                f"Query embedding dimension {query_vec.shape[0]} does not match "
                f"index dimension {self._vectors.shape[1]}."
            )

        similarities = self._vectors @ query_vec
        scored: list[tuple[float, int]] = []
        for idx, sim in enumerate(similarities.tolist()):
            chunk = self._chunks[idx]
            if language and chunk.metadata.language and chunk.metadata.language != language:
                continue
            if sim > self.min_score:
                scored.append((sim, idx))

        scored.sort(key=lambda item: item[0], reverse=True)
        return [
            ScoredChunk(
                chunk_id=self._chunks[idx].metadata.chunk_id,
                text=self._chunks[idx].text,
                retrieval_score=round(float(score), 6),
                retrieval_method=self.strategy_name,
                metadata=self._chunks[idx].metadata,
            )
            for score, idx in scored[:top_k]
        ]

    async def health_check(self) -> bool:
        return len(self._chunks) > 0 and self._vectors is not None
