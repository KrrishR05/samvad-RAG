"""
SAMVAD Speech Providers

Placeholder implementations for STT providers.
Each provider must implement BaseSpeechProvider.

Integration points:
  - SarvamSpeechProvider: Use Sarvam AI SDK for Indic-language STT.
  - ElevenLabsSpeechProvider: Use ElevenLabs API for STT.
"""

from __future__ import annotations

from typing import Optional

from app.core.errors import SpeechProcessingError, ConfigurationError
from app.pipeline.interfaces import TranscriptionResult
from app.speech.base import BaseSpeechProvider


class SarvamSpeechProvider(BaseSpeechProvider):
    """
    Sarvam AI speech-to-text provider.

    Primary STT provider for SAMVAD, chosen for its
    strong Indic-language support.

    TODO: Implement using the Sarvam AI SDK.
    Required config: SARVAM_API_KEY
    """

    provider_name = "sarvam"

    def __init__(self, api_key: Optional[str] = None) -> None:
        self.api_key = api_key
        if not self.api_key:
            raise ConfigurationError(
                "SARVAM_API_KEY is required for the Sarvam STT provider."
            )
        # TODO: Initialize Sarvam SDK client here.

    async def transcribe(
        self,
        audio_data: bytes,
        language: Optional[str] = None,
    ) -> TranscriptionResult:
        """
        TODO: Replace with actual Sarvam API call.

        Expected implementation:
          1. Send audio_data to Sarvam STT endpoint.
          2. Parse response into TranscriptionResult.
          3. Handle errors → raise SpeechProcessingError.
        """
        raise SpeechProcessingError(
            "Sarvam STT provider is not yet implemented."
        )

    async def health_check(self) -> bool:
        # TODO: Ping Sarvam API health endpoint.
        return False


class ElevenLabsSpeechProvider(BaseSpeechProvider):
    """
    ElevenLabs speech-to-text provider (alternative).

    TODO: Implement using the ElevenLabs SDK.
    Required config: ELEVENLABS_API_KEY
    """

    provider_name = "elevenlabs"

    def __init__(self, api_key: Optional[str] = None) -> None:
        self.api_key = api_key
        if not self.api_key:
            raise ConfigurationError(
                "ELEVENLABS_API_KEY is required for the ElevenLabs STT provider."
            )
        # TODO: Initialize ElevenLabs SDK client here.

    async def transcribe(
        self,
        audio_data: bytes,
        language: Optional[str] = None,
    ) -> TranscriptionResult:
        """
        TODO: Replace with actual ElevenLabs API call.
        """
        raise SpeechProcessingError(
            "ElevenLabs STT provider is not yet implemented."
        )

    async def health_check(self) -> bool:
        # TODO: Ping ElevenLabs API health endpoint.
        return False
