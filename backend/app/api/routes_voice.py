"""
SAMVAD API — Voice Routes

Voice query endpoint (accepts audio upload).
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, File, Form, Request, Response, UploadFile
from pydantic import BaseModel, Field

from app.core.config import get_settings
from app.core.logging import current_request_id, sanitize_request_id
from app.core.upload_validation import read_validated_audio_upload
from app.pipeline.orchestrator import get_orchestrator
from app.schemas.response import QueryResponse
from app.speech.tts import SarvamTTSProvider

router = APIRouter(prefix="/api/v1", tags=["voice"])


class SpeakRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=2000, description="Answer text to convert to speech")
    language: Optional[str] = Field(default=None, description="Language code (e.g. hi, en, ta)")
    speaker: Optional[str] = Field(default=None, description="Sarvam speaker name")


@router.post(
    "/voice/speak",
    summary="Synthesize speech audio from text (TTS via Sarvam Bulbul v3)",
)
async def speak_text(payload: SpeakRequest) -> Response:
    """Convert text into natural speech audio using Sarvam AI Bulbul v3."""
    tts = SarvamTTSProvider()
    audio_bytes = tts.synthesize(
        text=payload.text,
        language=payload.language,
        speaker=payload.speaker,
    )
    return Response(
        content=audio_bytes,
        media_type="audio/mpeg",
        headers={"Content-Disposition": "inline; filename=speech.mp3"},
    )


@router.post(
    "/voice/query",
    response_model=QueryResponse,
    summary="Submit a voice query",
)
async def submit_voice_query(
    request: Request,
    audio: UploadFile = File(..., description="Audio file (WAV/WebM/OGG/MP3/FLAC/M4A)"),
    request_id: Optional[str] = Form(default=None),
    language: Optional[str] = Form(default=None),
    retriever_strategy: Optional[str] = Form(default=None),
    top_k: Optional[int] = Form(default=None),
) -> QueryResponse:
    """
    Submit an audio recording to the SAMVAD voice pipeline.

    Validates audio upload size and format, executes transcription via the
    configured SpeechService, and runs retrieval and evidence grounding.
    """
    rid = (
        sanitize_request_id(request_id)
        if request_id
        else getattr(request.state, "request_id", None) or sanitize_request_id(None)
    )
    token = current_request_id.set(rid)
    try:
        settings = get_settings()
        audio_bytes = await read_validated_audio_upload(
            upload=audio,
            max_bytes=settings.max_audio_upload_bytes,
            request_id=rid,
        )
        orchestrator = get_orchestrator()
        return await orchestrator.run_voice_query(
            audio_data=audio_bytes,
            request_id=rid,
            language=language,
            retriever_strategy=retriever_strategy,
            top_k=top_k,
        )
    finally:
        current_request_id.reset(token)
