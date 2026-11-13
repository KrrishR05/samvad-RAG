"""
Tests — Relevance Reranker (Phase 3 — M3.1)
"""

import asyncio
import pytest

from app.core.config import Settings
from app.pipeline.interfaces import ScoredChunk
from app.retrieval.reranker import (
    LexicalAlignmentReranker,
    create_reranker_from_settings,
)


def test_lexical_alignment_reranker_orders_by_relevance():
    reranker = LexicalAlignmentReranker()

    candidates = [
        ScoredChunk(
            chunk_id="chunk-1",
            text="Apples and oranges are healthy fruits available in markets.",
            retrieval_score=0.8,
        ),
        ScoredChunk(
            chunk_id="chunk-2",
            text="Bengaluru is known as the Silicon Valley of India and Karnataka's capital.",
            retrieval_score=0.6,
        ),
        ScoredChunk(
            chunk_id="chunk-3",
            text="Karnataka is an Indian state with Bengaluru as its premier tech capital.",
            retrieval_score=0.5,
        ),
    ]

    # Query focused specifically on Bengaluru Karnataka capital
    query = "Bengaluru Karnataka capital"
    results = asyncio.run(reranker.rerank(query, candidates, top_k=2))

    assert len(results) == 2
    # The top results must be chunk-2 or chunk-3 (which mention Bengaluru and Karnataka)
    # and definitely NOT chunk-1 (which is about fruits)
    assert results[0].chunk_id in ("chunk-2", "chunk-3")
    assert results[1].chunk_id in ("chunk-2", "chunk-3")
    assert all(r.reranker_score is not None for r in results)
    assert results[0].reranker_score >= results[1].reranker_score


def test_reranker_handles_empty_candidates():
    reranker = LexicalAlignmentReranker()
    results = asyncio.run(reranker.rerank("any query", [], top_k=5))
    assert results == []


def test_create_reranker_from_settings():
    s_default = Settings(_env_file=None)
    reranker = create_reranker_from_settings(s_default)
    assert isinstance(reranker, LexicalAlignmentReranker)

    s_disabled = Settings(_env_file=None, reranker_provider="none")
    assert create_reranker_from_settings(s_disabled) is None
