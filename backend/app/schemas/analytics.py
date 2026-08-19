"""
SAMVAD Analytics Schemas

Data models for latency recording, benchmark storage,
and analytics API responses.
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class LatencyRecord(BaseModel):
    """
    A single pipeline execution's latency breakdown.

    Recorded after each completed (or failed) request.
    Fields that correspond to unimplemented stages remain None.
    """

    request_id: str

    stt_ms: Optional[float] = None
    query_processing_ms: Optional[float] = None
    embedding_ms: Optional[float] = None
    retrieval_ms: Optional[float] = None
    reranking_ms: Optional[float] = None
    generation_ms: Optional[float] = None
    guardrail_ms: Optional[float] = None

    total_ms: Optional[float] = None


class PercentileStats(BaseModel):
    """Percentile statistics for a set of latency values."""

    p50: Optional[float] = Field(default=None, description="50th percentile (median).")
    p70: Optional[float] = Field(default=None, description="70th percentile.")
    p100: Optional[float] = Field(default=None, description="100th percentile (max).")
    mean: Optional[float] = None
    min: Optional[float] = None
    max: Optional[float] = None
    count: int = 0


class StageLatencyStats(BaseModel):
    """Aggregated latency statistics broken down by pipeline stage."""

    stt: Optional[PercentileStats] = None
    query_processing: Optional[PercentileStats] = None
    embedding: Optional[PercentileStats] = None
    retrieval: Optional[PercentileStats] = None
    reranking: Optional[PercentileStats] = None
    generation: Optional[PercentileStats] = None
    guardrail: Optional[PercentileStats] = None
    total: Optional[PercentileStats] = None


class AnalyticsSummaryResponse(BaseModel):
    """Response for the analytics summary endpoint."""

    total_requests: int = 0
    stage_latency: Optional[StageLatencyStats] = None
    message: Optional[str] = Field(
        default=None,
        description="Human-readable status or notice.",
    )


class LatencyStatsResponse(BaseModel):
    """Response for the detailed latency endpoint."""

    total_records: int = 0
    overall: Optional[PercentileStats] = None
    by_stage: Optional[StageLatencyStats] = None
    message: Optional[str] = None
