"""
SAMVAD Retrieval — Lexical (BM25)

Placeholder for BM25-based lexical retrieval.

TODO: Implement using rank_bm25 or equivalent.
  1. Build a BM25 index over the chunked corpus.
  2. Tokenise the query.
  3. Score and return top-K candidates.
"""

from __future__ import annotations

from typing import Optional, Sequence

from app.core.errors import RetrievalError
from app.pipeline.interfaces import RetrievalCandidate
from app.retrieval.base import BaseRetriever


class LexicalRetriever(BaseRetriever):
    """
    Lexical (BM25) retrieval.

    TODO: Replace placeholder with real implementation.
    """

    strategy_name = "lexical"

    async def retrieve(
        self,
        query: str,
        top_k: int = 10,
        language: Optional[str] = None,
    ) -> Sequence[RetrievalCandidate]:
        # TODO: Implement BM25 retrieval.
        raise RetrievalError("Lexical retriever is not yet implemented.")

    async def health_check(self) -> bool:
        return False
