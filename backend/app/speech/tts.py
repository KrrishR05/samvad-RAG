"""
SAMVAD Text-to-Speech (TTS) Service

Powered by Sarvam AI Bulbul (v3).
Converts answer texts into high-quality Indic speech audio.
"""

from __future__ import annotations

import base64
import re
from typing import Optional

from app.core.config import get_settings
from app.core.errors import ConfigurationError, SpeechProcessingError

# Default speaker per language for bulbul:v3
DEFAULT_SPEAKERS: dict[str, str] = {
    "hi-IN": "aditya",
    "en-IN": "aditya",
    "ta-IN": "gokul",
    "te-IN": "kavitha",
    "bn-IN": "aditya",
    "mr-IN": "soham",
    "kn-IN": "kavitha",
    "gu-IN": "aditya",
    "pa-IN": "aditya",
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


def _split_text_into_chunks(text: str, max_chars: int = 2000) -> list[str]:
    """Split text into natural segments under the max_chars limit (preserving sentence structure)."""
    text = text.strip()
    if not text:
        return []
    if len(text) <= max_chars:
        return [text]

    chunks: list[str] = []
    # Split by double newline or single newline first
    paragraphs = re.split(r"\n+", text)
    current_chunk: list[str] = []
    current_len = 0

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        if len(para) > max_chars:
            # Paragraph exceeds limit: split by sentences
            sentences = re.split(r"(?<=[.!?।])\s+", para)
            for s in sentences:
                s = s.strip()
                if not s:
                    continue
                if current_len + len(s) + 1 > max_chars:
                    if current_chunk:
                        chunks.append(" ".join(current_chunk))
                        current_chunk = []
                        current_len = 0
                if len(s) > max_chars:
                    # Very long sentence without punctuation: split by words
                    words = s.split(" ")
                    for w in words:
                        if current_len + len(w) + 1 > max_chars:
                            if current_chunk:
                                chunks.append(" ".join(current_chunk))
                                current_chunk = []
                                current_len = 0
                        current_chunk.append(w)
                        current_len += len(w) + 1
                else:
                    current_chunk.append(s)
                    current_len += len(s) + 1
        else:
            if current_len + len(para) + 1 > max_chars:
                if current_chunk:
                    chunks.append(" ".join(current_chunk))
                    current_chunk = []
                    current_len = 0
            current_chunk.append(para)
            current_len += len(para) + 1

    if current_chunk:
        chunks.append(" ".join(current_chunk))

    return chunks


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
        Handles full responses cleanly, splitting into chunks if text exceeds model limits.
        """
        if not text.strip():
            raise SpeechProcessingError("Text cannot be empty for speech synthesis.")

        # Clean citations like [1], [2], [1, 2] and Markdown formatting before speaking
        clean_text = re.sub(r"\[\s*\d+(?:\s*,\s*\d+)*\s*\]", "", text)
        clean_text = clean_text.replace("•", ", ")
        clean_text = re.sub(r"[*#`_~>]", " ", clean_text)
        clean_text = re.sub(r"https?://\S+", "", clean_text)
        clean_text = re.sub(r"\s+", " ", clean_text).strip()

        if not clean_text:
            raise SpeechProcessingError("Text contained no speakable content after normalization.")

        lang_code = LANG_MAP.get(
            language or "",
            "hi-IN" if any("\u0900" <= c <= "\u097F" for c in clean_text) else "en-IN",
        )
        selected_speaker = speaker or DEFAULT_SPEAKERS.get(lang_code, "aditya")

        # Split text into chunks below Sarvam's 2500 character limit (using 2000 for safety)
        chunks = _split_text_into_chunks(clean_text, max_chars=2000)

        try:
            from sarvamai import SarvamAI

            client = SarvamAI(api_subscription_key=self.api_key)
            audio_segments: list[bytes] = []

            for chunk in chunks:
                resp = client.text_to_speech.convert(
                    text=chunk,
                    language_code=lang_code,
                    speaker=selected_speaker,
                    model=self.model_name,
                    output_audio_codec="mp3",
                )
                if resp.audios:
                    audio_segments.append(base64.b64decode(resp.audios[0]))

            if not audio_segments:
                raise SpeechProcessingError("No audio data returned by Sarvam TTS.")

            # Concat MP3 stream frames directly
            return b"".join(audio_segments)
        except Exception as exc:
            raise SpeechProcessingError(f"Sarvam TTS synthesis failed: {exc}") from exc
