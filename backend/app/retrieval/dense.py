"""
SAMVAD Retrieval — Dense

Placeholder for embedding-based dense retrieval.

TODO: Implement using FAISS or Qdrant.
  1. Load or connect to the pre-built vector index.
  2. Embed the query using the configured embedding model.
  3. Perform ANN search and return candidates.
"""

from __future__ import annotations

from typing import Optional, Sequence

from app.core.errors import RetrievalError
from app.pipeline.interfaces import RetrievalCandidate
from app.retrieval.base import BaseRetriever


class DenseRetriever(BaseRetriever):
    """
    Dense retrieval via approximate nearest neighbour search.

    Integration requirements:
      - Embedding model (e.g. sentence-transformers)
      - Pre-built vector index (FAISS / Qdrant)
      - EMBEDDING_MODEL and VECTOR_DB_PATH config

    TODO: Replace placeholder with real implementation.
    """

    strategy_name = "dense"

    async def retrieve(
        self,
        query: str,
        top_k: int = 10,
        language: Optional[str] = None,
    ) -> Sequence[RetrievalCandidate]:
        # TODO: Implement dense retrieval.
        raise RetrievalError("Dense retriever is not yet implemented.")

    async def health_check(self) -> bool:
        # TODO: Check index availability.
        return False
