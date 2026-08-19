"""
Tests — Pipeline State Machine
"""

import pytest

from app.pipeline.state import (
    InvalidTransitionError,
    PipelineState,
    VALID_TRANSITIONS,
)
from app.schemas.pipeline import PipelineStage, StageStatus


def test_initial_state():
    ps = PipelineState(request_id="r1")
    assert ps.current_stage == PipelineStage.IDLE
    assert ps.results == []
    assert not ps.is_terminal


def test_valid_transition():
    ps = PipelineState(request_id="r1")
    ps.transition_to(PipelineStage.VALIDATING)
    assert ps.current_stage == PipelineStage.VALIDATING


def test_invalid_transition():
    ps = PipelineState(request_id="r1")
    with pytest.raises(InvalidTransitionError):
        ps.transition_to(PipelineStage.GENERATING)


def test_begin_and_complete_stage():
    ps = PipelineState(request_id="r1")
    ps.begin_stage(PipelineStage.VALIDATING)
    result = ps.complete_stage(output="ok")

    assert result.stage == PipelineStage.VALIDATING
    assert result.status == StageStatus.COMPLETED
    assert result.duration_ms is not None
    assert result.duration_ms >= 0
    assert result.output == "ok"
    assert len(ps.results) == 1


def test_complete_stage_with_error():
    ps = PipelineState(request_id="r1")
    ps.begin_stage(PipelineStage.VALIDATING)
    result = ps.complete_stage(error="bad input")

    assert result.status == StageStatus.ERROR
    assert result.error == "bad input"


def test_terminal_states():
    ps = PipelineState(request_id="r1")
    ps.begin_stage(PipelineStage.VALIDATING)
    ps.complete_stage()
    ps.transition_to(PipelineStage.ABSTAINED)
    assert ps.is_terminal


def test_error_is_terminal():
    ps = PipelineState(request_id="r1")
    ps.begin_stage(PipelineStage.LISTENING)
    ps.complete_stage()
    ps.transition_to(PipelineStage.ERROR)
    assert ps.is_terminal
    # Cannot transition from terminal
    with pytest.raises(InvalidTransitionError):
        ps.transition_to(PipelineStage.COMPLETE)


def test_full_happy_path():
    """Walk through the ideal pipeline path."""
    ps = PipelineState(request_id="r1")

    stages = [
        PipelineStage.VALIDATING,
        PipelineStage.QUERY_ANALYSIS,
        PipelineStage.RETRIEVING,
        PipelineStage.RERANKING,
        PipelineStage.CONFIDENCE_CHECK,
        PipelineStage.GENERATING,
        PipelineStage.GROUNDING_CHECK,
        PipelineStage.COMPLETE,
    ]

    for stage in stages:
        if stage == PipelineStage.COMPLETE:
            ps.transition_to(stage)
        else:
            ps.begin_stage(stage)
            ps.complete_stage()

    assert ps.current_stage == PipelineStage.COMPLETE
    assert ps.is_terminal


def test_get_stage_result():
    ps = PipelineState(request_id="r1")
    ps.begin_stage(PipelineStage.VALIDATING)
    ps.complete_stage(output="validated")

    result = ps.get_stage_result(PipelineStage.VALIDATING)
    assert result is not None
    assert result.output == "validated"

    assert ps.get_stage_result(PipelineStage.GENERATING) is None
