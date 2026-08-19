"""
SAMVAD API — Voice Routes

Voice query endpoint (accepts audio upload).
"""

from __future__ import annotations

import uuid
from typing import Optional

from fastapi import APIRouter, File, Form, UploadFile

from app.pipeline.orchestrator import get_orchestrator
from app.schemas.response import QueryResponse

router = APIRouter(prefix="/api/v1", tags=["voice"])


@router.post(
    "/voice/query",
    response_model=QueryResponse,
    summary="Submit a voice query",
)
async def submit_voice_query(
    audio: UploadFile = File(..., description="Audio file (WAV/WebM/OGG)"),
    request_id: Optional[str] = Form(default=None),
    language: Optional[str] = Form(default=None),
) -> QueryResponse:
    """
    Submit an audio recording to the SAMVAD voice pipeline.

    The audio is sent to the configured STT provider for transcription,
    then processed through the full retrieval and generation pipeline.

    Until the STT provider and downstream services are connected,
    this endpoint returns a structured not_implemented response.
    """
    rid = request_id or str(uuid.uuid4())
    audio_bytes = await audio.read()

    orchestrator = get_orchestrator()
    return await orchestrator.run_voice_query(
        audio_data=audio_bytes,
        request_id=rid,
        language=language,
    )
