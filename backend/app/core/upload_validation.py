"""
SAMVAD Upload Validation

Bounded reading and MIME / magic-byte validation for uploaded audio files.
Prevents unbounded memory exhaustion (OOM DoS) and rejects spoofed non-audio files.
"""

from __future__ import annotations

from typing import Optional

from fastapi import UploadFile

from app.core.errors import InputValidationError, PayloadTooLargeError

_READ_CHUNK_BYTES = 64 * 1024

ALLOWED_AUDIO_MIME_TYPES: frozenset[str] = frozenset(
    {
        "audio/wav",
        "audio/x-wav",
        "audio/wave",
        "audio/vnd.wave",
        "audio/webm",
        "video/webm",  # Chromium MediaRecorder sometimes emits video/webm for Opus audio
        "audio/ogg",
        "application/ogg",
        "audio/mpeg",
        "audio/mp3",
        "audio/flac",
        "audio/x-flac",
        "audio/mp4",
        "audio/aac",
    }
)


def _matches_audio_magic(header: bytes) -> bool:
    """Check leading magic bytes for supported audio container formats."""
    if len(header) < 4:
        return False

    # WAV: "RIFF" .... "WAVE"
    if header[:4] == b"RIFF" and len(header) >= 12 and header[8:12] == b"WAVE":
        return True
    # WebM / Matroska (EBML)
    if header[:4] == b"\x1a\x45\xdf\xa3":
        return True
    # OGG / Opus
    if header[:4] == b"OggS":
        return True
    # FLAC
    if header[:4] == b"fLaC":
        return True
    # MP3 (ID3 tag or MPEG audio frame sync)
    if header[:3] == b"ID3":
        return True
    if header[0] == 0xFF and (header[1] & 0xE0) == 0xE0:
        return True
    # MP4 / M4A ("ftyp" at offset 4)
    if len(header) >= 8 and header[4:8] == b"ftyp":
        return True

    return False


def validate_audio_bytes(
    audio_bytes: bytes,
    content_type: Optional[str],
    request_id: Optional[str] = None,
) -> None:
    """Validate non-empty audio content, declared MIME type, and file signature."""
    if not audio_bytes:
        raise InputValidationError(
            "Uploaded audio file is empty.",
            request_id=request_id,
        )

    if content_type:
        base_mime = content_type.split(";", 1)[0].strip().lower()
        if base_mime and base_mime != "application/octet-stream" and base_mime not in ALLOWED_AUDIO_MIME_TYPES:
            raise InputValidationError(
                f"Unsupported audio content type: '{base_mime}'.",
                request_id=request_id,
            )

    if not _matches_audio_magic(audio_bytes[:16]):
        raise InputValidationError(
            "Uploaded file does not match a supported audio format (WAV, WebM, OGG, MP3, FLAC, M4A).",
            request_id=request_id,
        )


async def read_validated_audio_upload(
    upload: UploadFile,
    max_bytes: int,
    request_id: Optional[str] = None,
) -> bytes:
    """
    Stream-read an uploaded audio file up to *max_bytes* and validate its format.

    Raises:
        PayloadTooLargeError: If the upload exceeds *max_bytes*.
        InputValidationError: If the upload is empty or not a recognized audio file.
    """
    chunks: list[bytes] = []
    total_read = 0

    while True:
        chunk = await upload.read(_READ_CHUNK_BYTES)
        if not chunk:
            break
        total_read += len(chunk)
        if total_read > max_bytes:
            raise PayloadTooLargeError(
                f"Audio upload exceeds maximum allowed size of {max_bytes} bytes.",
                request_id=request_id,
            )
        chunks.append(chunk)

    audio_bytes = b"".join(chunks)
    validate_audio_bytes(
        audio_bytes=audio_bytes,
        content_type=upload.content_type,
        request_id=request_id,
    )
    return audio_bytes

