"""
SAMVAD Speech Service — Base

Abstract base class for all STT providers.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from app.pipeline.interfaces import TranscriptionResult


class BaseSpeechProvider(ABC):
    """
    Base class for speech-to-text providers.

    Concrete implementations:
      - SarvamSpeechProvider  (primary, Indic-language support)
      - ElevenLabsSpeechProvider (alternative)

    TODO: Implement concrete providers when API keys are available.
    """

    provider_name: str = "base"

    @abstractmethod
    async def transcribe(
        self,
        audio_data: bytes,
        language: Optional[str] = None,
    ) -> TranscriptionResult:
        """
        Transcribe audio bytes to text.

        Args:
            audio_data: Raw audio (WAV / WebM / OGG).
            language: ISO 639-1 hint.

        Returns:
            TranscriptionResult

        Raises:
            SpeechProcessingError
        """
        ...

    @abstractmethod
    async def health_check(self) -> bool:
        """Return True if the provider API is reachable."""
        ...
