"""
SAMVAD Generation — LLM Generator

Placeholder implementing the canonical AnswerGenerator protocol.
"""

from __future__ import annotations

from typing import Optional, Sequence

from app.core.errors import GenerationError
from app.pipeline.interfaces import GenerationResult, ScoredChunk


class LLMGenerator:
    """
    LLM-powered answer generator (Phase 2).

    Required config:
      - LLM_API_KEY
      - LLM_MODEL
    """

    async def generate(
        self,
        query: str,
        context: Sequence[ScoredChunk],
        language: Optional[str] = None,
    ) -> GenerationResult:
        raise GenerationError("LLM generator is not yet implemented.")
