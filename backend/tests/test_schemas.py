"""
Tests — Pydantic Schemas
"""

from app.schemas.request import QueryRequest, VoiceQueryRequest
from app.schemas.response import (
    Confidence,
    ConfidenceLevel,
    LatencyBreakdown,
    QueryResponse,
    QueryStatus,
    Source,
)
from app.schemas.pipeline import (
    ChunkMetadata,
    ChunkStrategy,
    PipelineStage,
    StageResult,
    StageStatus,
)
from app.schemas.analytics import LatencyRecord, PercentileStats


def test_query_request():
    req = QueryRequest(query="What is SAMVAD?")
    assert req.query == "What is SAMVAD?"
    assert req.request_id is None
    assert req.language is None


def test_voice_query_request():
    req = VoiceQueryRequest(language="hi")
    assert req.language == "hi"


def test_query_response_minimal():
    resp = QueryResponse(
        request_id="abc-123",
        status=QueryStatus.NOT_IMPLEMENTED,
    )
    assert resp.request_id == "abc-123"
    assert resp.status == QueryStatus.NOT_IMPLEMENTED
    assert resp.answer is None
    assert resp.sources == []


def test_source_model():
    src = Source(
        source_id="s1",
        text="Example passage.",
        metadata={"language": "en"},
        retrieval_score=0.95,
    )
    assert src.source_id == "s1"
    assert src.metadata["language"] == "en"


def test_confidence_model():
    c = Confidence(score=0.85, level=ConfidenceLevel.HIGH)
    assert c.score == 0.85


def test_latency_breakdown_defaults():
    lb = LatencyBreakdown()
    assert lb.stt_ms is None
    assert lb.total_ms is None


def test_chunk_metadata():
    cm = ChunkMetadata(
        chunk_id="c1",
        parent_document_id="d1",
        language="ta",
        chunk_strategy=ChunkStrategy.SEMANTIC,
        chunk_index=0,
        total_chunks=5,
    )
    assert cm.chunk_strategy == ChunkStrategy.SEMANTIC
    assert cm.language == "ta"


def test_stage_result():
    sr = StageResult(
        stage=PipelineStage.RETRIEVING,
        status=StageStatus.COMPLETED,
        duration_ms=42.5,
    )
    assert sr.duration_ms == 42.5


def test_latency_record():
    lr = LatencyRecord(
        request_id="r1",
        retrieval_ms=15.3,
        total_ms=120.0,
    )
    assert lr.retrieval_ms == 15.3
    assert lr.stt_ms is None


def test_percentile_stats_empty():
    ps = PercentileStats(count=0)
    assert ps.p50 is None
    assert ps.count == 0
