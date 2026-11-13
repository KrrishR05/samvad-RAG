"""
SAMVAD Text-to-Speech (TTS) Service

Powered by Sarvam AI Bulbul (v3).
Converts answer texts into high-quality Indic speech audio.
"""

from __future__ import annotations

import base64
from typing import Optional

from app.core.config import get_settings
from app.core.errors import ConfigurationError, SpeechProcessingError

# Default speaker per language for bulbul:v3
DEFAULT_SPEAKERS: dict[str, str] = {
    "hi-IN": "aditya",
    "en-IN": "aditi_en_stories",
    "ta-IN": "gokul_ta_narration",
    "te-IN": "kavitha_te_narration",
    "bn-IN": "arnab_bn_conversation",
    "mr-IN": "mrunal_mr_narration",
    "kn-IN": "chetan_kn_conversation",
    "gu-IN": "bhavik_gu_conversation",
    "pa-IN": "harpreet_pa_narration",
}

LANG_MAP: dict[str, str] = {
    "hi": "hi-IN",
    "en": "en-IN",
    "ta": "ta-IN",
    "te": "te-IN",
    "bn": "bn-IN",
    "mr": "mr-IN",
    "kn": "kn-IN",
    "gu": "gu-IN",
    "pa": "pa-IN",
}


class SarvamTTSProvider:
    """Sarvam AI Text-to-Speech provider using Bulbul v3."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: str = "bulbul:v3",
    ) -> None:
        settings = get_settings()
        self.api_key = api_key or settings.sarvam_api_key
        if not self.api_key:
            raise ConfigurationError("SARVAM_API_KEY is required for Sarvam TTS.")
        self.model_name = model_name

    def synthesize(
        self,
        text: str,
        language: Optional[str] = None,
        speaker: Optional[str] = None,
    ) -> bytes:
        """
        Synthesize text into MP3 audio bytes.
        """
        if not text.strip():
            raise SpeechProcessingError("Text cannot be empty for speech synthesis.")

        # Clean citations like [1], [2] before speaking so voice reads naturally
        import re
        clean_text = re.sub(r"\[\d+\]", "", text).strip()
        # Limit text length per synthesis chunk to ~500 chars for responsive streaming
        if len(clean_text) > 500:
            clean_text = clean_text[:500]

        lang_code = LANG_MAP.get(language or "", "hi-IN" if any("\u0900" <= c <= "\u097F" for c in clean_text) else "en-IN")
        selected_speaker = speaker or DEFAULT_SPEAKERS.get(lang_code, "aditya")

        try:
            from sarvamai import SarvamAI

            client = SarvamAI(api_subscription_key=self.api_key)
            resp = client.text_to_speech.convert(
                text=clean_text,
                language_code=lang_code,
                speaker=selected_speaker,
                model=self.model_name,
            )

            if not resp.audios:
                raise SpeechProcessingError("No audio data returned by Sarvam TTS.")

            return base64.b64decode(resp.audios[0])
        except Exception as exc:
            raise SpeechProcessingError(f"Sarvam TTS synthesis failed: {exc}") from exc

