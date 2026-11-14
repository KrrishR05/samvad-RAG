"""
SAMVAD Speech-Aware Normalizer (Phase 5 — M5.2)

Cleans and normalizes raw Speech-to-Text transcripts before pipeline retrieval:
- Removes verbal disfluencies and fillers (English & Indic: "um", "uh", "मतलब", "सुनो", "अरे").
- Eliminates stuttered / duplicate adjacent words ("the the", "क्या क्या").
- Normalizes Hinglish/transliterated stems to standard search keywords.
- Cleans punctuation and acoustic artifacts.
"""

from __future__ import annotations

import re
from typing import Optional

# Speech filler tokens to strip
_ENGLISH_FILLERS = [
    "you know", "sort of", "kind of", "i mean", "so yeah",
    "um", "uh", "er", "ah", "like", "actually", "basically",
]

_INDIC_FILLERS = [
    "मतलब", "यानी", "सुनो", "अरे", "अच्छा", "हाँ", "तो",
]

# Transliterated (Hinglish) keyword mappings for retrieval alignment
_HINGLISH_STEM_MAP = {
    "ke baare mein": "के बारे में",
    "ke baare me": "के बारे में",
    "kya hai": "क्या है",
    "kaise karein": "कैसे करें",
    "kaise": "कैसे",
    "kya": "क्या",
    "batao": "बताओ",
    "bataiye": "बताइए",
    "kyun": "क्यों",
    "kaun": "कौन",
    "kahan": "कहाँ",
}


class SpeechNormalizer:
    """Normalizes raw speech transcripts for robust RAG retrieval."""

    def __init__(
        self,
        strip_fillers: bool = True,
        dedup_stutters: bool = True,
        normalize_hinglish: bool = True,
    ) -> None:
        self.strip_fillers = strip_fillers
        self.dedup_stutters = dedup_stutters
        self.normalize_hinglish = normalize_hinglish

        filler_patterns = [r"\b" + re.escape(f) + r"\b" for f in _ENGLISH_FILLERS]
        self._en_filler_re = re.compile("|".join(filler_patterns), re.IGNORECASE)

        indic_patterns = [r"(?:\b|^|\s)" + re.escape(f) + r"(?:[,\s\.\?!;:]|$)" for f in _INDIC_FILLERS]
        self._indic_filler_re = re.compile("|".join(indic_patterns))

    def normalize(self, transcript: str, language: Optional[str] = None) -> str:
        """Clean speech transcript text."""
        if not transcript or not transcript.strip():
            return ""

        text = transcript.strip()

        # 1. Strip fillers
        if self.strip_fillers:
            text = self._en_filler_re.sub(" ", text)
            # Repeat once to catch adjacent fillers like "सुनो, मतलब"
            text = self._indic_filler_re.sub(" ", text)
            text = self._indic_filler_re.sub(" ", text)

        # 2. Deduplicate stutter words (e.g. "what what is" -> "what is", "the the" -> "the")
        if self.dedup_stutters:
            text = re.sub(r"\b(\w+)(?:\s+\1\b)+", r"\1", text, flags=re.IGNORECASE)

        # 3. Transliterated / Hinglish stem expansion
        if self.normalize_hinglish:
            lowered = text.lower()
            sorted_stems = sorted(_HINGLISH_STEM_MAP.items(), key=lambda x: len(x[0]), reverse=True)
            for stem, replacement in sorted_stems:
                if stem in lowered:
                    text = f"{text} {replacement}"
                    break

        # 4. Clean extra spaces and leading/trailing punctuation artifacts
        text = re.sub(r"\s+", " ", text).strip()
        text = re.sub(r"^[,\.\?!;:\s]+", "", text).strip()

        return text or transcript.strip()
