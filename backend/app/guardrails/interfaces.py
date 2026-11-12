"""
SAMVAD Guardrails — Interface Stubs

Guardrail implementations matching the canonical GuardrailService protocol.
Unimplemented guardrails fail explicitly with NotImplementedError rather than
returning misleading `passed=True` results.
"""

from __future__ import annotations

from typing import Optional, Sequence

from app.pipeline.interfaces import GuardrailResult, ScoredChunk


class InputGuard:
    """Validates basic query input quality before pipeline execution."""

    guardrail_name = "input_guard"

    async def check(
        self,
        *,
        query: Optional[str] = None,
        answer: Optional[str] = None,
        context: Optional[Sequence[ScoredChunk]] = None,
        confidence: Optional[float] = None,
    ) -> GuardrailResult:
        if query is None or len(query.strip()) == 0:
            return GuardrailResult(
                passed=False,
                reason="Empty or whitespace-only query.",
                action="abstain",
            )
        if "\x00" in query:
            return GuardrailResult(
                passed=False,
                reason="Query contains invalid null-byte characters.",
                action="abstain",
            )
        return GuardrailResult(passed=True)


class RelevanceGuard:
    """Checks whether retrieved context is sufficiently relevant (Phase 4)."""

    guardrail_name = "relevance_guard"

    async def check(
        self,
        *,
        query: Optional[str] = None,
        answer: Optional[str] = None,
        context: Optional[Sequence[ScoredChunk]] = None,
        confidence: Optional[float] = None,
    ) -> GuardrailResult:
        raise NotImplementedError("RelevanceGuard is not yet implemented.")


class ConfidenceGuard:
    """Prevents generation when retrieval confidence is too low (Phase 4)."""

    guardrail_name = "confidence_guard"

    async def check(
        self,
        *,
        query: Optional[str] = None,
        answer: Optional[str] = None,
        context: Optional[Sequence[ScoredChunk]] = None,
        confidence: Optional[float] = None,
    ) -> GuardrailResult:
        raise NotImplementedError("ConfidenceGuard is not yet implemented.")


class GroundingGuard:
    """Verifies that the generated answer is grounded in evidence (Phase 4)."""

    guardrail_name = "grounding_guard"

    async def check(
        self,
        *,
        query: Optional[str] = None,
        answer: Optional[str] = None,
        context: Optional[Sequence[ScoredChunk]] = None,
        confidence: Optional[float] = None,
    ) -> GuardrailResult:
        raise NotImplementedError("GroundingGuard is not yet implemented.")
