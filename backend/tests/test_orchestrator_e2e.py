"""
Tests — End-to-End Text Pipeline Orchestrator
"""

from __future__ import annotations

import asyncio
from typing import Optional, Sequence

import pytest

from app.analytics.metrics import MetricsStore
from app.core.config import Settings
from app.core.errors import InputValidationError, PipelineTimeoutError
from app.ingestion.chunker import DocumentChunk
from app.pipeline.interfaces import GenerationResult, ScoredChunk
from app.pipeline.orchestrator import PipelineOrchestrator
from app.retrieval.dense import DenseRetriever
from app.retrieval.hybrid import HybridRetriever
from app.retrieval.lexical import LexicalRetriever
from app.schemas.pipeline import ChunkMetadata, PipelineStage
from app.schemas.response import QueryStatus


class _StubGenerator:
    provider_name = "stub"
    model_name = "stub-1"

    async def generate(
        self,
        query: str,
        context: Sequence[ScoredChunk],
        language: Optional[str] = None,
    ) -> GenerationResult:
        return GenerationResult(
            answer=f"Grounded answer citing {context[0].chunk_id} [1].",
            grounded=True,
            confidence_score=0.88,
            sources_used=[context[0].chunk_id],
        )


class _SlowRetriever:
    strategy_name = "slow"

    async def retrieve(
        self,
        query: str,
        top_k: int = 10,
        language: Optional[str] = None,
    ) -> Sequence[ScoredChunk]:
        await asyncio.sleep(0.3)
        return []

    async def health_check(self) -> bool:
        return True


def _sample_chunks() -> list[DocumentChunk]:
    return [
        DocumentChunk(
            text="SAMVAD supports multilingual evidence retrieval across English and Hindi.",
            metadata=ChunkMetadata(chunk_id="c1", parent_document_id="doc1", language="en"),
        ),
        DocumentChunk(
            text="संवाद हिंदी और अंग्रेजी दस्तावेज़ों से प्रमाणित उत्तर खोजता है।",
            metadata=ChunkMetadata(chunk_id="c2", parent_document_id="doc2", language="hi"),
        ),
    ]


@pytest.mark.asyncio
async def test_unconfigured_orchestrator_returns_not_implemented():
    orch = PipelineOrchestrator()
    res = await orch.run_text_query("What is SAMVAD?")
    assert res.status == QueryStatus.NOT_IMPLEMENTED


@pytest.mark.asyncio
async def test_orchestrator_without_generator_retrieves_honestly():
    chunks = _sample_chunks()
    lexical = LexicalRetriever(chunks)
    store = MetricsStore()
    orch = PipelineOrchestrator(
        retrievers={"lexical": lexical},
        default_retriever_key="lexical",
        generator=None,
        metrics_store=store,
    )
    res = await orch.run_text_query("multilingual evidence retrieval")
    assert res.status == QueryStatus.NOT_IMPLEMENTED
    assert "LLM_PROVIDER" in (res.message or "")
    assert len(res.sources) >= 1
    assert res.sources[0].source_id == "c1"
    assert store.total_requests == 0


@pytest.mark.asyncio
async def test_orchestrator_happy_path_and_metrics_recorded():
    chunks = _sample_chunks()
    lexical = LexicalRetriever(chunks)
    dense = DenseRetriever()
    await dense.build_index(chunks)
    hybrid = HybridRetriever(dense_retriever=dense, lexical_retriever=lexical)
    store = MetricsStore()

    orch = PipelineOrchestrator(
        retrievers={"hybrid": hybrid, "lexical": lexical, "dense": dense},
        default_retriever_key="hybrid",
        generator=_StubGenerator(),
        metrics_store=store,
    )
    res = await orch.run_text_query("multilingual evidence retrieval", language="en")
    assert res.status == QueryStatus.COMPLETED
    assert res.grounded is True
    assert res.retrieval_method == "hybrid"
    assert res.sources[0].metadata["citation_index"] == 1
    assert res.sources[0].metadata["is_cited"] is True
    assert res.latency is not None and res.latency.total_ms is not None
    assert any(stage.stage == PipelineStage.GENERATING for stage in res.stages)
    assert store.total_requests == 1

    # Strategy override
    lex_res = await orch.run_text_query(
        "multilingual evidence retrieval",
        retriever_strategy="lexical",
    )
    assert lex_res.retrieval_method == "lexical"

    # Unknown strategy raises validation error
    with pytest.raises(InputValidationError):
        await orch.run_text_query("anything", retriever_strategy="unknown_mode")


@pytest.mark.asyncio
async def test_orchestrator_abstains_when_no_context_retrieved():
    lexical = LexicalRetriever([])
    orch = PipelineOrchestrator(
        retrievers={"lexical": lexical},
        default_retriever_key="lexical",
        generator=_StubGenerator(),
        metrics_store=MetricsStore(),
    )
    res = await orch.run_text_query("nonexistent topic")
    assert res.status == QueryStatus.ABSTAINED
    assert res.grounded is False
    assert res.sources == []


@pytest.mark.asyncio
async def test_orchestrator_pipeline_timeout():
    cfg = Settings(pipeline_timeout_seconds=0.05, stage_timeout_seconds=0.04)
    orch = PipelineOrchestrator(
        retrievers={"slow": _SlowRetriever()},
        default_retriever_key="slow",
        generator=_StubGenerator(),
        settings=cfg,
        metrics_store=MetricsStore(),
    )
    with pytest.raises(PipelineTimeoutError):
        await orch.run_text_query("trigger timeout")


@pytest.mark.asyncio
async def test_orchestrator_handles_samvad_self_identity_query():
    from app.retrieval.query_analyzer import IndicQueryAnalyzer
    lexical = LexicalRetriever([])  # Empty index!
    orch = PipelineOrchestrator(
        retrievers={"lexical": lexical},
        default_retriever_key="lexical",
        query_analyzer=IndicQueryAnalyzer(),
        generator=_StubGenerator(),
        metrics_store=MetricsStore(),
    )
    res = await orch.run_text_query("What is SAMVAD and what are its capabilities?")
    assert res.status == QueryStatus.COMPLETED
    assert res.grounded is True
    assert len(res.sources) == 1
    assert res.sources[0].source_id == "samvad-platform-core-overview"
    assert "samvad-platform-core-overview" in res.answer
