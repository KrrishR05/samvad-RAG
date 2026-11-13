"""
SAMVAD Speech Providers

Conforming implementations for SpeechService:
  - GeminiSpeechProvider: Multilingual audio transcription via Google Gemini REST API.
  - SarvamSpeechProvider: Placeholder for Sarvam AI Indic STT.
  - ElevenLabsSpeechProvider: Placeholder for ElevenLabs STT.
"""

from __future__ import annotations

import base64
from typing import Optional

import httpx

from app.core.config import Settings
from app.core.errors import ConfigurationError, SpeechProcessingError
from app.pipeline.interfaces import SpeechService, TranscriptionResult


class GeminiSpeechProvider:
    """Multilingual Speech-to-Text provider using Google Gemini's audio processing."""

    provider_name = "gemini"

    def __init__(
        self,
        *,
        api_key: str,
        model_name: str = "gemini-3.5-flash-lite",
        base_url: str = "https://generativelanguage.googleapis.com/v1beta",
        timeout_seconds: float = 20.0,
    ) -> None:
        if not api_key:
            raise ConfigurationError("LLM_API_KEY is required for GeminiSpeechProvider.")
        self.api_key = api_key
        self.model_name = model_name
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds

    async def transcribe(
        self,
        audio_data: bytes,
        language: Optional[str] = None,
    ) -> TranscriptionResult:
        if not audio_data:
            raise SpeechProcessingError("Empty audio data received.")

        # Determine audio MIME type from header magic bytes
        mime_type = "audio/webm"
        if audio_data.startswith(b"RIFF"):
            mime_type = "audio/wav"
        elif audio_data.startswith(b"OggS"):
            mime_type = "audio/ogg"
        elif audio_data[:3] == b"ID3" or (
            len(audio_data) >= 2 and audio_data[:2] in (b"\xff\xfb", b"\xff\xf3", b"\xff\xf2")
        ):
            mime_type = "audio/mp3"
        elif audio_data.startswith(b"fLaC"):
            mime_type = "audio/flac"

        b64_audio = base64.b64encode(audio_data).decode("utf-8")
        lang_prompt = f"The spoken language is expected to be '{language}'. " if language else ""
        prompt = (
            f"Transcribe this spoken audio verbatim. {lang_prompt}\n"
            "Rules:\n"
            "1. Output ONLY the raw spoken text transcript in the language spoken.\n"
            "2. Do not add explanations, prefixes, metadata, or quotation marks.\n"
            "3. If there is no discernible speech or only silence/static, output only: [SILENCE]"
        )

        payload = {
            "contents": [
                {
                    "parts": [
                        {"inline_data": {"mime_type": mime_type, "data": b64_audio}},
                        {"text": prompt},
                    ]
                }
            ],
            "generationConfig": {"temperature": 0.0},
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                resp = await client.post(
                    f"{self.base_url}/models/{self.model_name}:generateContent?key={self.api_key}",
                    headers={"Content-Type": "application/json"},
                    json=payload,
                )
                resp.raise_for_status()
                data = resp.json()
        except Exception as exc:
            raise SpeechProcessingError(f"Gemini speech transcription failed: {exc}") from exc

        try:
            parts = data["candidates"][0]["content"]["parts"]
            text = "".join(part.get("text", "") for part in parts).strip()
        except Exception as exc:
            raise SpeechProcessingError("Malformed response from Gemini STT.") from exc

        if text == "[SILENCE]" or not text:
            return TranscriptionResult(
                text="",
                language=language,
                confidence=0.0,
                provider=self.provider_name,
            )

        return TranscriptionResult(
            text=text,
            language=language,
            confidence=0.95,
            provider=self.provider_name,
        )

    async def health_check(self) -> bool:
        return bool(self.api_key)


class SarvamSpeechProvider:
    """Sarvam AI speech-to-text provider using saaras:v3."""

    provider_name = "sarvam"

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: str = "saaras:v3",
        timeout_seconds: float = 20.0,
    ) -> None:
        self.api_key = api_key
        if not self.api_key:
            raise ConfigurationError(
                "SARVAM_API_KEY is required for the Sarvam STT provider."
            )
        self.model_name = model_name
        self.timeout_seconds = timeout_seconds

    async def transcribe(
        self,
        audio_data: bytes,
        language: Optional[str] = None,
    ) -> TranscriptionResult:
        if not audio_data:
            raise SpeechProcessingError("Empty audio data received.")

        # Map ISO language code (e.g. 'hi') to Sarvam format ('hi-IN')
        lang_code = "unknown"
        if language:
            clean_lang = language.strip().lower()
            lang_map = {
                "hi": "hi-IN",
                "bn": "bn-IN",
                "ta": "ta-IN",
                "te": "te-IN",
                "kn": "kn-IN",
                "ml": "ml-IN",
                "mr": "mr-IN",
                "gu": "gu-IN",
                "pa": "pa-IN",
                "od": "od-IN",
                "en": "en-IN",
            }
            lang_code = lang_map.get(
                clean_lang, clean_lang if "-IN" in clean_lang else "unknown"
            )

        try:
            from sarvamai import SarvamAI

            client = SarvamAI(api_subscription_key=self.api_key)
            resp = client.speech_to_text.transcribe(
                file=audio_data,
                model=self.model_name,
                language_code=lang_code,
            )
            transcript = (getattr(resp, "transcript", "") or "").strip()
            detected_lang = getattr(resp, "language_code", language)
            return TranscriptionResult(
                text=transcript,
                language=detected_lang,
                confidence=0.95,
                provider=self.provider_name,
            )
        except Exception as exc:
            raise SpeechProcessingError(f"Sarvam STT failed: {exc}") from exc

    async def health_check(self) -> bool:
        return bool(self.api_key)


class ElevenLabsSpeechProvider:
    """ElevenLabs speech-to-text provider (Phase 4)."""

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


def create_speech_service_from_settings(settings: Settings) -> Optional[SpeechService]:
    """Construct a configured SpeechService provider or None if unconfigured."""
    stt_provider = (
        settings.stt_provider.value
        if hasattr(settings.stt_provider, "value")
        else str(settings.stt_provider or "")
    ).strip().lower()

    if stt_provider == "sarvam" and settings.sarvam_api_key:
        return SarvamSpeechProvider(api_key=settings.sarvam_api_key)
    if stt_provider == "elevenlabs" and settings.elevenlabs_api_key:
        return ElevenLabsSpeechProvider(api_key=settings.elevenlabs_api_key)
    if stt_provider == "gemini" and settings.llm_api_key:
        model = settings.llm_model or "gemini-3.5-flash-lite"
        timeout = min(settings.stage_timeout_seconds, settings.pipeline_timeout_seconds)
        return GeminiSpeechProvider(
            api_key=settings.llm_api_key,
            model_name=model,
            timeout_seconds=timeout,
        )

    return None
