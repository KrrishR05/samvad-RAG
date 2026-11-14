"""
Tests — Phase 5: Query SSE Streaming (M5.3)
"""

import pytest
from app.pipeline.interfaces import GenerationResult, ScoredChunk
from app.pipeline.orchestrator import PipelineOrchestrator
from app.retrieval.lexical import LexicalRetriever


class _StubGen:
    async def generate(self, query: str, context, **kwargs) -> GenerationResult:
        return GenerationResult(
            answer="Grounded answer citing chunk [1].",
            grounded=True,
            sources_used=[context[0].chunk_id],
        )


@pytest.mark.asyncio
async def test_stream_text_query_yields_stage_events_and_complete():
    chunk = ScoredChunk(chunk_id="chunk-1", text="Nokvirae platform documentation.", retrieval_score=0.9)
    lexical = LexicalRetriever([chunk])
    orch = PipelineOrchestrator(
        retrievers={"lexical": lexical},
        default_retriever_key="lexical",
        generator=_StubGen(),
    )

    events = []
    async for evt in orch.stream_text_query("What is Nokvirae?"):
        events.append(evt)

    event_types = [e.get("event") for e in events]
    assert "stage_start" in event_types
    assert "stage_complete" in event_types
    assert "complete" in event_types

    # Find complete event
    complete_evt = next(e for e in events if e.get("event") == "complete")
    assert complete_evt["response"]["status"] == "completed"
    assert "Grounded answer citing chunk [1]." in complete_evt["response"]["answer"]

