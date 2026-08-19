"""
SAMVAD Pipeline Schemas

Models describing pipeline execution state, stage results,
and the data that flows between pipeline stages.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class PipelineStage(str, Enum):
    """All stages in the SAMVAD processing pipeline."""

    IDLE = "idle"
    LISTENING = "listening"
    TRANSCRIBING = "transcribing"
    VALIDATING = "validating"
    QUERY_ANALYSIS = "query_analysis"
    RETRIEVING = "retrieving"
    RERANKING = "reranking"
    CONFIDENCE_CHECK = "confidence_check"
    GENERATING = "generating"
    GROUNDING_CHECK = "grounding_check"
    COMPLETE = "complete"
    ERROR = "error"
    RETRYING = "retrying"
    FALLBACK = "fallback"
    ABSTAINED = "abstained"


class StageStatus(str, Enum):
    """Status of an individual pipeline stage."""

    PENDING = "pending"
    ACTIVE = "active"
    COMPLETED = "completed"
    ERROR = "error"
    SKIPPED = "skipped"
    ABSTAINED = "abstained"


class StageResult(BaseModel):
    """Result produced by a single pipeline stage."""

    stage: PipelineStage
    status: StageStatus = StageStatus.PENDING
    duration_ms: Optional[float] = Field(
        default=None,
        description="Wall-clock time for this stage in milliseconds.",
    )
    output: Optional[Any] = Field(
        default=None,
        description="Stage-specific output payload.",
    )
    error: Optional[str] = Field(
        default=None,
        description="Error message if the stage failed.",
    )
    retries: int = Field(
        default=0,
        description="Number of retries executed for this stage.",
    )


class ChunkStrategy(str, Enum):
    """
    Supported chunking strategies.

    The actual implementations will be added later.
    The enum is defined now so that schemas and metadata
    can reference strategy types from the start.
    """

    WHOLE_PASSAGE = "whole_passage"
    FIXED_SIZE = "fixed_size"
    SEMANTIC = "semantic"
    SLIDING_WINDOW = "sliding_window"


class ChunkMetadata(BaseModel):
    """
    Metadata for a single document chunk.

    Designed to support multi-strategy chunking and
    multilingual/Indic-oriented data from MSMARCO-XI.
    """

    chunk_id: str
    parent_document_id: Optional[str] = None
    language: Optional[str] = Field(
        default=None,
        description="ISO 639-1 language code of the chunk content.",
    )
    chunk_strategy: Optional[ChunkStrategy] = None
    chunk_index: Optional[int] = Field(
        default=None,
        description="Position of this chunk within its parent document.",
    )
    total_chunks: Optional[int] = None
    char_count: Optional[int] = None
    token_count: Optional[int] = None
    extra: dict[str, Any] = Field(
        default_factory=dict,
        description="Flexible storage for dataset-specific fields.",
    )
