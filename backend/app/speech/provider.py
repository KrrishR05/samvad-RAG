"""
SAMVAD Speech Providers

Placeholder implementations for STT providers conforming to SpeechService.
"""

from __future__ import annotations

from typing import Optional

from app.core.errors import ConfigurationError, SpeechProcessingError
from app.pipeline.interfaces import TranscriptionResult


class SarvamSpeechProvider:
    """Sarvam AI speech-to-text provider (Phase 5)."""

    provider_name = "sarvam"

    def __init__(self, api_key: Optional[str] = None) -> None:
        self.api_key = api_key
        if not self.api_key:
            raise ConfigurationError(
                "SARVAM_API_KEY is required for the Sarvam STT provider."
            )

    async def transcribe(
        self,
        audio_data: bytes,
        language: Optional[str] = None,
    ) -> TranscriptionResult:
        raise SpeechProcessingError("Sarvam STT provider is not yet implemented.")

    async def health_check(self) -> bool:
        return False


class ElevenLabsSpeechProvider:
    """ElevenLabs speech-to-text provider (Phase 5)."""

    provider_name = "elevenlabs"

    def __init__(self, api_key: Optional[str] = None) -> None:
        self.api_key = api_key
        if not self.api_key:
            raise ConfigurationError(
                "ELEVENLABS_API_KEY is required for the ElevenLabs STT provider."
            )

    async def transcribe(
        self,
        audio_data: bytes,
        language: Optional[str] = None,
    ) -> TranscriptionResult:
        raise SpeechProcessingError("ElevenLabs STT provider is not yet implemented.")

    async def health_check(self) -> bool:
        return False
