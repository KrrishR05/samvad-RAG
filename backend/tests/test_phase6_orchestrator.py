"""
Tests — Phase 6 Orchestrator Adaptive Routing & Caching Integration
"""

import pytest

from app.core.config import Settings
from app.generation.generator import GenerationResult
from app.pipeline.interfaces import AnalyzedQuery, ScoredChunk
from app.pipeline.orchestrator import PipelineOrchestrator
from app.retrieval.cache import RetrievalCache
from app.retrieval.router import AdaptiveRouter
from app.schemas.pipeline import ChunkMetadata


class MockGenerator:
    async def generate(self, query: str, context, language=None, intensity="standard"):
        return GenerationResult(
            answer="Grounded answer grounded in evidence [1].",
            grounded=True,
            confidence_score=0.9,
        )


class MockRetriever:
    def __init__(self, name: str):
        self.strategy_name = name
        self.call_count = 0

    async def retrieve(self, query: str, top_k: int = 10, language: str | None = None):
        self.call_count += 1
        return [
            ScoredChunk(
                chunk_id=f"{self.strategy_name}_doc",
                text=f"Content retrieved via {self.strategy_name} for {query}.",
                retrieval_score=0.9,
                retrieval_method=self.strategy_name,
                metadata=ChunkMetadata(
                    chunk_id=f"{self.strategy_name}_doc",
                    parent_document_id="doc1",
                    language="en",
                    extra={"title": "Test Title"},
                ),
            )
        ]

    async def health_check(self) -> bool:
        return True


@pytest.mark.asyncio
async def test_orchestrator_adaptive_routing():
    lex_ret = MockRetriever("lexical")
    dense_ret = MockRetriever("dense")
    hybrid_ret = MockRetriever("hybrid")

    router = AdaptiveRouter()
    orch = PipelineOrchestrator(
        retrievers={"lexical": lex_ret, "dense": dense_ret, "hybrid": hybrid_ret},
        default_retriever_key="hybrid",
        query_router=router,
        generator=MockGenerator(),
        settings=Settings(enable_guardrails=False),
    )

    # 1. Exact acronym query -> should route to lexical
    resp1 = await orch.run_text_query("ISRO mission update")
    assert resp1.retrieval_method == "lexical"
    assert lex_ret.call_count == 1
    assert dense_ret.call_count == 0

    # 2. Short conceptual question -> should route to dense
    resp2 = await orch.run_text_query("What is machine learning?")
    assert resp2.retrieval_method == "dense"
    assert dense_ret.call_count == 1


@pytest.mark.asyncio
async def test_orchestrator_retrieval_caching():
    hybrid_ret = MockRetriever("hybrid")
    cache = RetrievalCache()

    orch = PipelineOrchestrator(
        retrievers={"hybrid": hybrid_ret},
        default_retriever_key="hybrid",
        retrieval_cache=cache,
        generator=MockGenerator(),
        settings=Settings(enable_guardrails=False, enable_retrieval_cache=True),
    )

    # Query 1: Cold cache
    resp1 = await orch.run_text_query("Quantum computing basics")
    assert hybrid_ret.call_count == 1
    # Check stage output
    ret_stage1 = next(st for st in resp1.stages if st.stage.value == "retrieving")
    assert ret_stage1.output.get("cache_hit") is False

    # Query 2: Repeated query -> Warm cache hit
    resp2 = await orch.run_text_query("Quantum computing basics")
    assert hybrid_ret.call_count == 1  # Retriever not called again!
    ret_stage2 = next(st for st in resp2.stages if st.stage.value == "retrieving")
    assert ret_stage2.output.get("cache_hit") is True
