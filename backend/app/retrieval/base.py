"""
SAMVAD Retrieval — Base

Abstract base class for all retrieval strategies.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional, Sequence

from app.pipeline.interfaces import RetrievalCandidate


class BaseRetriever(ABC):
    """
    Base retriever interface.

    Subclasses:
      - DenseRetriever   (embedding-based)
      - LexicalRetriever (BM25)
      - HybridRetriever  (fusion of dense + lexical)

    TODO: Implement concrete retrievers.
    """

    strategy_name: str = "base"

    @abstractmethod
    async def retrieve(
        self,
        query: str,
        top_k: int = 10,
        language: Optional[str] = None,
    ) -> Sequence[RetrievalCandidate]:
        """Retrieve top_k candidates for the given query."""
        ...

    @abstractmethod
    async def health_check(self) -> bool:
        """Return True if the underlying index is available."""
        ...
