"""
SAMVAD Retrieval — Reranker

Placeholder conforming to the canonical Reranker protocol (Phase 3).
"""

from __future__ import annotations

from typing import Sequence

from app.core.errors import RetrievalError
from app.pipeline.interfaces import ScoredChunk


class CrossEncoderReranker:
    """Rerank candidates using a cross-encoder model."""

    async def rerank(
        self,
        query: str,
        candidates: Sequence[ScoredChunk],
        top_k: int = 5,
    ) -> Sequence[ScoredChunk]:
        raise RetrievalError("Reranker is not yet implemented.")
