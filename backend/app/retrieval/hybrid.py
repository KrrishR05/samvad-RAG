"""
SAMVAD Retrieval — Hybrid

Placeholder conforming to the canonical Retriever protocol (Phase 2).
"""

from __future__ import annotations

from typing import Optional, Sequence

from app.core.errors import RetrievalError
from app.pipeline.interfaces import Retriever, ScoredChunk


class HybridRetriever:
    """Hybrid retrieval combining dense and lexical strategies."""

    strategy_name = "hybrid"

    def __init__(
        self,
        dense_retriever: Optional[Retriever] = None,
        lexical_retriever: Optional[Retriever] = None,
        dense_weight: float = 0.7,
        lexical_weight: float = 0.3,
    ) -> None:
        self.dense_retriever = dense_retriever
        self.lexical_retriever = lexical_retriever
        self.dense_weight = dense_weight
        self.lexical_weight = lexical_weight

    async def retrieve(
        self,
        query: str,
        top_k: int = 10,
        language: Optional[str] = None,
    ) -> Sequence[ScoredChunk]:
        raise RetrievalError("Hybrid retriever is not yet implemented.")

    async def health_check(self) -> bool:
        return False
