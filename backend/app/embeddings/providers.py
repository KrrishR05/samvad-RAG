"""
SAMVAD Embeddings — Providers

Supports:
  - OpenAICompatibleEmbeddingProvider (Ollama /v1/embeddings, OpenAI, vLLM, etc.)
  - LocalTfidfSVDProvider (deterministic local baseline via scikit-learn; zero API keys)
"""

from __future__ import annotations

from typing import Optional, Sequence

import httpx
import numpy as np
from sklearn.decomposition import TruncatedSVD
from sklearn.feature_extraction.text import TfidfVectorizer

from app.core.errors import ConfigurationError, RetrievalError


def _l2_normalize_rows(matrix: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    norms = np.where(norms == 0.0, 1.0, norms)
    return (matrix / norms).astype(np.float32)


class OpenAICompatibleEmbeddingProvider:
    """HTTP embedding provider compatible with OpenAI, Ollama, and vLLM `/embeddings`."""

    def __init__(
        self,
        *,
        model_name: str,
        base_url: str = "http://localhost:11434/v1",
        api_key: Optional[str] = None,
        dimension: int = 0,
        timeout_seconds: float = 15.0,
    ) -> None:
        if not model_name:
            raise ConfigurationError("EMBEDDING_MODEL is required for OpenAI-compatible embeddings.")
        self.model_name = model_name
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.dimension = dimension
        self.timeout_seconds = timeout_seconds

    def _headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    async def embed_documents(self, texts: Sequence[str]) -> np.ndarray:
        if not texts:
            return np.zeros((0, self.dimension), dtype=np.float32)
        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                resp = await client.post(
                    f"{self.base_url}/embeddings",
                    headers=self._headers(),
                    json={"model": self.model_name, "input": list(texts)},
                )
                resp.raise_for_status()
                payload = resp.json()
        except Exception as exc:
            raise RetrievalError(f"Embedding request failed: {exc}") from exc

        data = sorted(payload["data"], key=lambda item: item["index"])
        vectors = np.asarray([item["embedding"] for item in data], dtype=np.float32)
        if vectors.ndim != 2 or vectors.shape[0] != len(texts):
            raise RetrievalError("Unexpected embedding response shape.")
        self.dimension = int(vectors.shape[1])
        return _l2_normalize_rows(vectors)

    async def embed_query(self, text: str) -> np.ndarray:
        matrix = await self.embed_documents([text])
        return matrix[0]

    async def health_check(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                resp = await client.get(f"{self.base_url}/models", headers=self._headers())
                return resp.status_code < 500
        except Exception:
            return False


class LocalTfidfSVDProvider:
    """
    Deterministic local dense projection using character/word TF-IDF + TruncatedSVD.

    Useful as a zero-API, reproducible local baseline when no neural embedding
    server/model is configured. Must be fit on corpus documents before querying.
    """

    def __init__(self, target_dimension: int = 128) -> None:
        if target_dimension <= 0:
            raise ValueError("target_dimension must be positive.")
        self.model_name = f"local-tfidf-svd-{target_dimension}"
        self._target_dimension = target_dimension
        self.dimension = target_dimension
        self._vectorizer = TfidfVectorizer(
            analyzer="char_wb",
            ngram_range=(3, 5),
            min_df=1,
            max_features=20000,
        )
        self._svd: Optional[TruncatedSVD] = None
        self._is_fitted = False

    def fit(self, texts: Sequence[str]) -> None:
        if not texts:
            self._is_fitted = False
            return
        tfidf = self._vectorizer.fit_transform(texts)
        n_samples, n_features = tfidf.shape
        n_components = min(self._target_dimension, max(1, min(n_samples, n_features) - 1))
        if n_components >= 1 and min(n_samples, n_features) > 1:
            self._svd = TruncatedSVD(n_components=n_components, random_state=42)
            self._svd.fit(tfidf)
            self.dimension = n_components
        else:
            self._svd = None
            self.dimension = int(n_features)
        self._is_fitted = True

    async def embed_documents(self, texts: Sequence[str]) -> np.ndarray:
        if not texts:
            return np.zeros((0, self.dimension), dtype=np.float32)
        if not self._is_fitted:
            self.fit(texts)
        tfidf = self._vectorizer.transform(texts)
        dense = (
            self._svd.transform(tfidf)
            if self._svd is not None
            else tfidf.toarray()
        )
        return _l2_normalize_rows(np.asarray(dense, dtype=np.float32))

    async def embed_query(self, text: str) -> np.ndarray:
        if not self._is_fitted:
            raise RetrievalError("LocalTfidfSVDProvider has not been fit on any corpus.")
        matrix = await self.embed_documents([text])
        return matrix[0]

    async def health_check(self) -> bool:
        return self._is_fitted

