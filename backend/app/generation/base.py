"""
SAMVAD Generation — Base

Abstract base class for answer generators.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional, Sequence

from app.pipeline.interfaces import (
    GenerationResult,
    RerankResult,
    RetrievalCandidate,
)


class BaseGenerator(ABC):
    """
    Base class for grounded answer generation.

    TODO: Implement LLM-based generator.
    """

    @abstractmethod
    async def generate(
        self,
        query: str,
        context: Sequence[RerankResult] | Sequence[RetrievalCandidate],
        language: Optional[str] = None,
    ) -> GenerationResult:
        """
        Generate a grounded answer.

        Args:
            query: The user's question.
            context: Retrieved and (optionally) reranked passages.
            language: Target language for the answer.

        Returns:
            GenerationResult with the answer and grounding info.

        Raises:
            GenerationError
        """
        ...
