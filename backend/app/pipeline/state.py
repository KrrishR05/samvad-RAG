"""
SAMVAD Pipeline State Machine

Defines valid pipeline state transitions and provides a lightweight
state tracker for a single pipeline execution.
"""

from __future__ import annotations

import time
from typing import Optional

from app.schemas.pipeline import PipelineStage, StageResult, StageStatus

# ---------------------------------------------------------------------------
# Valid state transitions
# ---------------------------------------------------------------------------

VALID_TRANSITIONS: dict[PipelineStage, set[PipelineStage]] = {
    PipelineStage.IDLE: {
        PipelineStage.LISTENING,
        PipelineStage.VALIDATING,  # text queries skip listening
    },
    PipelineStage.LISTENING: {
        PipelineStage.TRANSCRIBING,
        PipelineStage.ERROR,
    },
    PipelineStage.TRANSCRIBING: {
        PipelineStage.VALIDATING,
        PipelineStage.ERROR,
        PipelineStage.ABSTAINED,
    },
    PipelineStage.VALIDATING: {
        PipelineStage.QUERY_ANALYSIS,
        PipelineStage.ERROR,
        PipelineStage.ABSTAINED,
    },
    PipelineStage.QUERY_ANALYSIS: {
        PipelineStage.RETRIEVING,
        PipelineStage.ERROR,
    },
    PipelineStage.RETRIEVING: {
        PipelineStage.RERANKING,
        PipelineStage.CONFIDENCE_CHECK,  # skip reranking if not configured
        PipelineStage.ERROR,
        PipelineStage.RETRYING,
        PipelineStage.FALLBACK,
    },
    PipelineStage.RERANKING: {
        PipelineStage.CONFIDENCE_CHECK,
        PipelineStage.ERROR,
        PipelineStage.RETRYING,
    },
    PipelineStage.CONFIDENCE_CHECK: {
        PipelineStage.GENERATING,
        PipelineStage.ABSTAINED,  # confidence too low
        PipelineStage.ERROR,
    },
    PipelineStage.GENERATING: {
        PipelineStage.GROUNDING_CHECK,
        PipelineStage.ERROR,
    },
    PipelineStage.GROUNDING_CHECK: {
        PipelineStage.COMPLETE,
        PipelineStage.ABSTAINED,
        PipelineStage.ERROR,
    },
    # Terminal & recovery states
    PipelineStage.RETRYING: {
        PipelineStage.RETRIEVING,
        PipelineStage.RERANKING,
        PipelineStage.ERROR,
    },
    PipelineStage.FALLBACK: {
        PipelineStage.CONFIDENCE_CHECK,
        PipelineStage.ABSTAINED,
        PipelineStage.ERROR,
    },
    PipelineStage.ERROR: set(),       # terminal
    PipelineStage.COMPLETE: set(),    # terminal
    PipelineStage.ABSTAINED: set(),   # terminal
}


class InvalidTransitionError(Exception):
    """Raised when an invalid state transition is attempted."""


class PipelineState:
    """
    Tracks the current stage and accumulated results
    for a single pipeline execution.
    """

    def __init__(self, request_id: str) -> None:
        self.request_id = request_id
        self.current_stage = PipelineStage.IDLE
        self.results: list[StageResult] = []
        self._stage_start: Optional[float] = None

    # ------------------------------------------------------------------
    # State transitions
    # ------------------------------------------------------------------

    def transition_to(self, next_stage: PipelineStage) -> None:
        """
        Move the pipeline to *next_stage*, validating the transition.

        Raises InvalidTransitionError if the transition is not allowed.
        """
        allowed = VALID_TRANSITIONS.get(self.current_stage, set())
        if next_stage not in allowed:
            raise InvalidTransitionError(
                f"Cannot transition from {self.current_stage.value} "
                f"to {next_stage.value}."
            )
        self.current_stage = next_stage

    def begin_stage(self, stage: PipelineStage) -> None:
        """Mark the start of a new stage (with validation)."""
        self.transition_to(stage)
        self._stage_start = time.perf_counter()

    def complete_stage(
        self,
        output: object = None,
        error: Optional[str] = None,
    ) -> StageResult:
        """
        Finalise the current stage and record its result.

        Returns the StageResult for the completed stage.
        """
        elapsed_ms: Optional[float] = None
        if self._stage_start is not None:
            elapsed_ms = (time.perf_counter() - self._stage_start) * 1000.0

        status = StageStatus.ERROR if error else StageStatus.COMPLETED
        result = StageResult(
            stage=self.current_stage,
            status=status,
            duration_ms=elapsed_ms,
            output=output,
            error=error,
        )
        self.results.append(result)
        self._stage_start = None
        return result

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @property
    def is_terminal(self) -> bool:
        return self.current_stage in {
            PipelineStage.COMPLETE,
            PipelineStage.ERROR,
            PipelineStage.ABSTAINED,
        }

    def get_stage_result(self, stage: PipelineStage) -> Optional[StageResult]:
        """Return the result for a specific stage, if recorded."""
        for r in reversed(self.results):
            if r.stage == stage:
                return r
        return None
