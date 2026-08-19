"""
SAMVAD API — Query Routes

Text-based query endpoint.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter

from app.pipeline.orchestrator import get_orchestrator
from app.schemas.request import QueryRequest
from app.schemas.response import QueryResponse

router = APIRouter(prefix="/api/v1", tags=["query"])


@router.post(
    "/query",
    response_model=QueryResponse,
    summary="Submit a text query",
)
async def submit_query(body: QueryRequest) -> QueryResponse:
    """
    Submit a natural-language text query to the SAMVAD pipeline.

    Until the retrieval and generation modules are connected,
    this endpoint returns a structured not_implemented response.
    """
    request_id = body.request_id or str(uuid.uuid4())
    orchestrator = get_orchestrator()
    return await orchestrator.run_text_query(
        query=body.query,
        request_id=request_id,
        language=body.language,
    )
