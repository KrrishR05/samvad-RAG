"""
SAMVAD Response Schemas

All outbound response models for the SAMVAD API.
Designed to be stable so the frontend can integrate without breaking changes.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class QueryStatus(str, Enum):
    """Top-level status of a query response."""

    PROCESSING = "processing"
    COMPLETED = "completed"
    ABSTAINED = "abstained"
    ERROR = "error"
    NOT_IMPLEMENTED = "not_implemented"


class ConfidenceLevel(str, Enum):
    """Human-readable confidence bucket."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INSUFFICIENT = "insufficient"


# ---------------------------------------------------------------------------
# Sub-models
# ---------------------------------------------------------------------------

class Source(BaseModel):
    """A single retrieved source/passage used for grounding the answer."""

    source_id: str = Field(..., description="Unique identifier for this source.")
    passage_id: Optional[str] = Field(
        default=None,
        description="Parent passage or document ID from the corpus.",
    )
    text: str = Field(..., description="Passage text content.")
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description=(
            "Flexible metadata: language, chunk_strategy, chunk_position, "
            "query_id, is_selected, etc."
        ),
    )
    retrieval_score: Optional[float] = Field(
        default=None,
        description="Score from the initial retrieval stage.",
    )
    reranker_score: Optional[float] = Field(
        default=None,
        description="Score from the reranking stage.",
    )


class Confidence(BaseModel):
    """Confidence assessment for the generated answer."""

    score: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Numeric confidence score [0, 1].",
    )
    level: Optional[ConfidenceLevel] = Field(
        default=None,
        description="Categorical confidence level.",
    )


class LatencyBreakdown(BaseModel):
    """
    Stage-level latency in milliseconds.

    All fields are optional — a stage that has not yet been implemented
    simply remains None.  Never populate with fake values.
    """

    stt_ms: Optional[float] = Field(default=None, description="Speech-to-text latency.")
    query_processing_ms: Optional[float] = Field(default=None)
    embedding_ms: Optional[float] = Field(default=None)
    retrieval_ms: Optional[float] = Field(default=None)
    reranking_ms: Optional[float] = Field(default=None)
    generation_ms: Optional[float] = Field(default=None)
    guardrail_ms: Optional[float] = Field(default=None)
    total_ms: Optional[float] = Field(default=None, description="End-to-end latency.")


# ---------------------------------------------------------------------------
# Top-level responses
# ---------------------------------------------------------------------------

class QueryResponse(BaseModel):
    """
    Stable response envelope for all query endpoints.

    The frontend relies on this shape — extend carefully.
    """

    request_id: str = Field(..., description="Unique request identifier.")
    status: QueryStatus = Field(..., description="Current processing status.")
    transcript: Optional[str] = Field(
        default=None,
        description="STT transcript (voice queries only).",
    )
    answer: Optional[str] = Field(
        default=None,
        description="Generated answer text.",
    )
    grounded: Optional[bool] = Field(
        default=None,
        description="Whether the answer passed the grounding check.",
    )
    confidence: Optional[Confidence] = Field(
        default=None,
        description="Confidence assessment.",
    )
    sources: list[Source] = Field(
        default_factory=list,
        description="Retrieved sources used for grounding.",
    )
    latency: Optional[LatencyBreakdown] = Field(
        default=None,
        description="Per-stage latency breakdown.",
    )
    message: Optional[str] = Field(
        default=None,
        description="Human-readable status/info message.",
    )


class HealthResponse(BaseModel):
    """Health-check response."""

    status: str = Field(default="healthy")
    service: str = Field(default="samvad-api")
    version: str = Field(default="0.1.0")
    environment: str = Field(default="development")
