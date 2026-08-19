"""
SAMVAD Guardrails — Interface Stubs

Placeholder implementations for all guardrail types.

TODO: Implement each guardrail with actual logic.
"""

from __future__ import annotations

from typing import Optional, Sequence

from app.guardrails.base import BaseGuardrail
from app.pipeline.interfaces import GuardrailResult, RetrievalCandidate


class InputGuard(BaseGuardrail):
    """
    Validates input quality before processing.

    Checks for:
      - Empty audio / no detected speech
      - Empty transcript
      - Invalid request format
      - STT failures

    TODO: Implement concrete validation rules.
    """

    guardrail_name = "input_guard"

    async def check(
        self,
        *,
        query: Optional[str] = None,
        answer: Optional[str] = None,
        context: Optional[Sequence[RetrievalCandidate]] = None,
        confidence: Optional[float] = None,
    ) -> GuardrailResult:
        # Basic input validation (can be used now)
        if query is not None and len(query.strip()) == 0:
            return GuardrailResult(
                passed=False,
                reason="Empty or whitespace-only query.",
                action="abstain",
            )
        return GuardrailResult(passed=True)


class RelevanceGuard(BaseGuardrail):
    """
    Checks whether retrieved context is sufficiently relevant.

    TODO: Implement relevance threshold logic based on
    retrieval scores and/or reranker scores.
    """

    guardrail_name = "relevance_guard"

    async def check(
        self,
        *,
        query: Optional[str] = None,
        answer: Optional[str] = None,
        context: Optional[Sequence[RetrievalCandidate]] = None,
        confidence: Optional[float] = None,
    ) -> GuardrailResult:
        # TODO: Implement relevance checking.
        return GuardrailResult(passed=True)


class ConfidenceGuard(BaseGuardrail):
    """
    Prevents generation when retrieval confidence is too low.

    TODO: Implement confidence threshold logic.
    """

    guardrail_name = "confidence_guard"

    async def check(
        self,
        *,
        query: Optional[str] = None,
        answer: Optional[str] = None,
        context: Optional[Sequence[RetrievalCandidate]] = None,
        confidence: Optional[float] = None,
    ) -> GuardrailResult:
        # TODO: Implement confidence threshold.
        return GuardrailResult(passed=True)


class GroundingGuard(BaseGuardrail):
    """
    Verifies that the generated answer is grounded in evidence.

    TODO: Implement grounding verification.
    """

    guardrail_name = "grounding_guard"

    async def check(
        self,
        *,
        query: Optional[str] = None,
        answer: Optional[str] = None,
        context: Optional[Sequence[RetrievalCandidate]] = None,
        confidence: Optional[float] = None,
    ) -> GuardrailResult:
        # TODO: Implement grounding check.
        return GuardrailResult(passed=True)
