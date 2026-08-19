"""
SAMVAD Guardrails — Base

Abstract base and concrete placeholder guardrails.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional, Sequence

from app.pipeline.interfaces import GuardrailResult, RetrievalCandidate


class BaseGuardrail(ABC):
    """Base guardrail interface."""

    guardrail_name: str = "base"

    @abstractmethod
    async def check(
        self,
        *,
        query: Optional[str] = None,
        answer: Optional[str] = None,
        context: Optional[Sequence[RetrievalCandidate]] = None,
        confidence: Optional[float] = None,
    ) -> GuardrailResult:
        ...
