"""
SAMVAD Generation — LLM Generator

Placeholder for the LLM-based answer generator.

TODO: Implement with the chosen LLM provider.
  1. Format retrieved context into a prompt.
  2. Call the LLM API.
  3. Parse the response.
  4. Assess grounding quality.
  5. Return GenerationResult.
"""

from __future__ import annotations

from typing import Optional, Sequence

from app.core.errors import GenerationError
from app.generation.base import BaseGenerator
from app.pipeline.interfaces import (
    GenerationResult,
    RerankResult,
    RetrievalCandidate,
)


class LLMGenerator(BaseGenerator):
    """
    LLM-powered answer generator.

    Required config:
      - LLM_API_KEY
      - LLM_MODEL

    TODO: Replace placeholder with real LLM integration.
    """

    async def generate(
        self,
        query: str,
        context: Sequence[RerankResult] | Sequence[RetrievalCandidate],
        language: Optional[str] = None,
    ) -> GenerationResult:
        # TODO: Implement LLM-based generation with grounding.
        raise GenerationError("LLM generator is not yet implemented.")
