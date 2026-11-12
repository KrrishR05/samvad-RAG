"""
SAMVAD Retrieval — Dense

Placeholder conforming to the canonical Retriever protocol (Phase 2).
"""

from __future__ import annotations

from typing import Optional, Sequence

from app.core.errors import RetrievalError
from app.pipeline.interfaces import ScoredChunk


class DenseRetriever:
    """Dense retrieval via approximate nearest neighbour search."""

    strategy_name = "dense"

    async def retrieve(
        self,
        query: str,
        top_k: int = 10,
        language: Optional[str] = None,
    ) -> Sequence[ScoredChunk]:
        raise RetrievalError("Dense retriever is not yet implemented.")

    async def health_check(self) -> bool:
        return False
