"""
SAMVAD Embeddings — Canonical Protocol
"""

from __future__ import annotations

from typing import Protocol, Sequence, runtime_checkable

import numpy as np


@runtime_checkable
class EmbeddingProvider(Protocol):
    """Provider-independent interface for text embeddings."""

    model_name: str
    dimension: int

    async def embed_documents(self, texts: Sequence[str]) -> np.ndarray:
        """Return float32 array of shape (len(texts), dimension)."""
        ...

    async def embed_query(self, text: str) -> np.ndarray:
        """Return float32 1-D array of shape (dimension,)."""
        ...

    async def health_check(self) -> bool:
        """Return True if the embedding provider is ready."""
        ...

