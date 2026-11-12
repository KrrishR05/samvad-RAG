"""
Tests — Hybrid Reciprocal Rank Fusion Retriever
"""

from __future__ import annotations

from typing import Optional, Sequence

import pytest

from app.core.errors import RetrievalError
from app.ingestion.chunker import DocumentChunk
from app.pipeline.interfaces import ScoredChunk
from app.retrieval.dense import DenseRetriever
from app.retrieval.hybrid import HybridRetriever
from app.retrieval.lexical import LexicalRetriever
from app.schemas.pipeline import ChunkMetadata


class _FailingRetriever:
    strategy_name = "failing"

    async def retrieve(
        self,
        query: str,
        top_k: int = 10,
        language: Optional[str] = None,
    ) -> Sequence[ScoredChunk]:
        raise RetrievalError("Simulated leg failure.")

    async def health_check(self) -> bool:
        return False


def _chunks() -> list[DocumentChunk]:
    return [
        DocumentChunk(
            text="Reciprocal Rank Fusion merges ranked candidate lists from sparse and dense search.",
            metadata=ChunkMetadata(chunk_id="c_rrf", parent_document_id="d1", language="en"),
        ),
        DocumentChunk(
            text="BM25 computes exact lexical term frequency and inverse document frequency.",
            metadata=ChunkMetadata(chunk_id="c_bm25", parent_document_id="d2", language="en"),
        ),
        DocumentChunk(
            text="Ocean tides are governed primarily by lunar gravitational pull.",
            metadata=ChunkMetadata(chunk_id="c_ocean", parent_document_id="d3", language="en"),
        ),
    ]


@pytest.mark.asyncio
async def test_hybrid_rrf_combines_dense_and_lexical():
    chunks = _chunks()
    lexical = LexicalRetriever(chunks)
    dense = DenseRetriever()
    await dense.build_index(chunks)

    hybrid = HybridRetriever(dense_retriever=dense, lexical_retriever=lexical)
    assert await hybrid.health_check() is True

    results = await hybrid.retrieve("Reciprocal Rank Fusion sparse dense", top_k=2)
    assert len(results) == 2
    assert results[0].chunk_id == "c_rrf"
    assert results[0].retrieval_method == "hybrid"
    assert results[0].retrieval_score > results[1].retrieval_score


@pytest.mark.asyncio
async def test_hybrid_degrades_gracefully_on_single_leg_failure():
    chunks = _chunks()
    lexical = LexicalRetriever(chunks)
    hybrid = HybridRetriever(dense_retriever=_FailingRetriever(), lexical_retriever=lexical)

    results = await hybrid.retrieve("BM25 lexical", top_k=2)
    assert results
    assert results[0].chunk_id == "c_bm25"


@pytest.mark.asyncio
async def test_hybrid_raises_when_all_legs_fail():
    hybrid = HybridRetriever(
        dense_retriever=_FailingRetriever(),
        lexical_retriever=_FailingRetriever(),
    )
    with pytest.raises(RetrievalError):
        await hybrid.retrieve("anything")

