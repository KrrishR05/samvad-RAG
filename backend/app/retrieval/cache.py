"""
SAMVAD Retrieval — Semantic Retrieval Cache (Phase 6 — M6.2)

High-performance, thread-safe, TTL-bounded LRU cache for retrieval candidates.
Eliminates duplicate vector embedding and BM25 scoring for repetitive queries.
"""

from __future__ import annotations

import hashlib
import re
import threading
import time
from collections import OrderedDict
from typing import Optional, Sequence

from app.pipeline.interfaces import ScoredChunk


def _normalize_cache_key_text(text: str) -> str:
    """Normalize text by folding case, collapsing spaces, and stripping outer punctuation."""
    folded = text.lower().strip()
    return re.sub(r"\s+", " ", folded)


class RetrievalCache:
    """
    Thread-safe LRU cache for retrieval candidate chunks with TTL expiration.
    """

    def __init__(
        self,
        *,
        max_entries: int = 1000,
        ttl_seconds: float = 300.0,
    ) -> None:
        if max_entries <= 0:
            raise ValueError("max_entries must be positive.")
        self.max_entries = max_entries
        self.ttl_seconds = ttl_seconds

        self._cache: OrderedDict[str, tuple[list[ScoredChunk], float]] = OrderedDict()
        self._lock = threading.Lock()

        # Telemetry
        self._hits = 0
        self._misses = 0
        self._evictions = 0

    def _make_key(
        self,
        query: str,
        language: Optional[str],
        strategy: str,
        top_k: int,
    ) -> str:
        norm_q = _normalize_cache_key_text(query)
        norm_lang = (language or "").strip().lower()
        norm_strat = strategy.strip().lower()
        raw = f"{norm_q}::{norm_lang}::{norm_strat}::{top_k}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def get(
        self,
        query: str,
        language: Optional[str],
        strategy: str,
        top_k: int,
    ) -> Optional[list[ScoredChunk]]:
        """Retrieve cached candidates if present and not expired."""
        key = self._make_key(query, language, strategy, top_k)
        now = time.perf_counter()

        with self._lock:
            if key not in self._cache:
                self._misses += 1
                return None

            chunks, timestamp = self._cache[key]
            if (now - timestamp) > self.ttl_seconds:
                # Expired
                del self._cache[key]
                self._misses += 1
                return None

            # Move to end (LRU touch)
            self._cache.move_to_end(key)
            self._hits += 1
            # Return fresh shallow copies so callers cannot mutate cache internal state
            return [
                ScoredChunk(
                    chunk_id=c.chunk_id,
                    text=c.text,
                    retrieval_score=c.retrieval_score,
                    reranker_score=c.reranker_score,
                    retrieval_method=c.retrieval_method,
                    metadata=c.metadata,
                )
                for c in chunks
            ]

    def set(
        self,
        query: str,
        language: Optional[str],
        strategy: str,
        top_k: int,
        results: Sequence[ScoredChunk],
    ) -> None:
        """Store retrieval results in the cache."""
        key = self._make_key(query, language, strategy, top_k)
        now = time.perf_counter()

        with self._lock:
            if key in self._cache:
                self._cache.move_to_end(key)
            elif len(self._cache) >= self.max_entries:
                self._cache.popitem(last=False)
                self._evictions += 1

            self._cache[key] = (list(results), now)

    def invalidate(self) -> None:
        """Evict all entries (called on document ingestion or deletion)."""
        with self._lock:
            self._cache.clear()

    @property
    def stats(self) -> dict[str, float | int]:
        """Cache hit rate and size telemetry."""
        with self._lock:
            total = self._hits + self._misses
            hit_ratio = (self._hits / total) if total > 0 else 0.0
            return {
                "hits": self._hits,
                "misses": self._misses,
                "hit_ratio": round(hit_ratio, 4),
                "size": len(self._cache),
                "max_entries": self.max_entries,
                "evictions": self._evictions,
            }

