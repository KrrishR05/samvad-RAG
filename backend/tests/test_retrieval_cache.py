"""
Tests — Semantic Retrieval Cache (Phase 6 — M6.2)
"""

import time
import pytest

from app.pipeline.interfaces import ScoredChunk
from app.retrieval.cache import RetrievalCache


def _sample_chunks():
    return [
        ScoredChunk(chunk_id="c1", text="Chunk 1 content", retrieval_score=0.9),
        ScoredChunk(chunk_id="c2", text="Chunk 2 content", retrieval_score=0.8),
    ]


def test_cache_miss_and_hit():
    cache = RetrievalCache(max_entries=10, ttl_seconds=60.0)
    chunks = _sample_chunks()

    # Initial get -> miss
    res = cache.get(query="chandrayaan 3", language="en", strategy="hybrid", top_k=5)
    assert res is None
    assert cache.stats["hits"] == 0
    assert cache.stats["misses"] == 1

    # Set cache
    cache.set(query="chandrayaan 3", language="en", strategy="hybrid", top_k=5, results=chunks)
    assert cache.stats["size"] == 1

    # Second get with same normalized query (case, spacing) -> hit
    res2 = cache.get(query="   Chandrayaan   3  ", language="en", strategy="hybrid", top_k=5)
    assert res2 is not None
    assert len(res2) == 2
    assert res2[0].chunk_id == "c1"
    assert cache.stats["hits"] == 1
    assert cache.stats["hit_ratio"] == 0.5


def test_cache_ttl_expiration():
    # Very short TTL
    cache = RetrievalCache(max_entries=10, ttl_seconds=0.05)
    cache.set(query="test query", language="hi", strategy="lexical", top_k=3, results=_sample_chunks())

    # Immediately hits
    assert cache.get("test query", "hi", "lexical", 3) is not None

    # Wait for expiration
    time.sleep(0.06)
    assert cache.get("test query", "hi", "lexical", 3) is None


def test_cache_lru_eviction():
    cache = RetrievalCache(max_entries=2, ttl_seconds=60.0)
    cache.set(query="q1", language="en", strategy="hybrid", top_k=5, results=_sample_chunks())
    cache.set(query="q2", language="en", strategy="hybrid", top_k=5, results=_sample_chunks())

    # Access q1 to make q2 oldest
    assert cache.get("q1", "en", "hybrid", 5) is not None

    # Insert q3 -> should evict q2
    cache.set(query="q3", language="en", strategy="hybrid", top_k=5, results=_sample_chunks())

    assert cache.get("q1", "en", "hybrid", 5) is not None
    assert cache.get("q2", "en", "hybrid", 5) is None
    assert cache.get("q3", "en", "hybrid", 5) is not None
    assert cache.stats["evictions"] == 1


def test_cache_invalidation():
    cache = RetrievalCache(max_entries=10, ttl_seconds=60.0)
    cache.set(query="query one", language="en", strategy="dense", top_k=5, results=_sample_chunks())
    cache.set(query="query two", language="hi", strategy="lexical", top_k=5, results=_sample_chunks())
    assert cache.stats["size"] == 2

    cache.invalidate()
    assert cache.stats["size"] == 0
    assert cache.get("query one", "en", "dense", 5) is None

