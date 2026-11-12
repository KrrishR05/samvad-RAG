"""
SAMVAD Ingestion — Text Normalization & Hashing

Unicode NFC normalization (critical for consistent Indic Devanagari/Konkani/Hindi
codepoint representation) and deterministic SHA-256 content hashing.
"""

from __future__ import annotations

import hashlib
import re
import unicodedata

_MULTI_NEWLINE_RE = re.compile(r"\n{3,}")
_INLINE_WS_RE = re.compile(r"[ \t\f\v]+")


def normalize_text(text: str) -> str:
    """
    Normalize text across English and Indic scripts without altering semantics.

    - Applies Unicode NFC normalization.
    - Strips BOM and null bytes.
    - Normalizes line endings to '\\n' and collapses excessive whitespace.
    """
    if not text:
        return ""
    cleaned = text.replace("\ufeff", "").replace("\x00", "")
    cleaned = unicodedata.normalize("NFC", cleaned)
    cleaned = cleaned.replace("\r\n", "\n").replace("\r", "\n")

    lines = [_INLINE_WS_RE.sub(" ", line).strip() for line in cleaned.split("\n")]
    joined = "\n".join(lines)
    joined = _MULTI_NEWLINE_RE.sub("\n\n", joined)
    return joined.strip()


def sha256_text(text: str) -> str:
    """Compute hex SHA-256 hash of normalized UTF-8 text."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

