"""
SAMVAD Retrieval — Reranker

Placeholder for the reranking stage.

TODO: Implement cross-encoder or model-based reranker.
  1. Receive initial retrieval candidates.
  2. Score each candidate against the query with a cross-encoder.
  3. Re-sort and return top-K.
"""

from __future__ import annotations

from typing import Sequence

from app.core.errors import RetrievalError
from app.pipeline.interfaces import RetrievalCandidate, RerankResult


class CrossEncoderReranker:
    """
    Rerank candidates using a cross-encoder model.

    TODO: Replace placeholder with real implementation.
    Required: a cross-encoder model (e.g. ms-marco-MiniLM).
    """

    async def rerank(
        self,
        query: str,
        candidates: Sequence[RetrievalCandidate],
        top_k: int = 5,
    ) -> Sequence[RerankResult]:
        """
        TODO: Implement cross-encoder reranking.
        """
        raise RetrievalError("Reranker is not yet implemented.")
