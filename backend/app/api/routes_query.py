"""
SAMVAD API — Query Routes

Text-based query endpoint.
"""

from __future__ import annotations

from fastapi import APIRouter, Request

from app.core.logging import current_request_id, sanitize_request_id
from app.pipeline.orchestrator import get_orchestrator
from app.schemas.request import QueryRequest
from app.schemas.response import QueryResponse

router = APIRouter(prefix="/api/v1", tags=["query"])


@router.post(
    "/query",
    response_model=QueryResponse,
    summary="Submit a text query",
)
async def submit_query(request: Request, body: QueryRequest) -> QueryResponse:
    """
    Submit a natural-language text query to the SAMVAD pipeline.

    Runs validation, query analysis, configured retrieval, optional reranking,
    and LLM answer generation with inline source citations when configured.
    """
    rid = (
        sanitize_request_id(body.request_id)
        if body.request_id
        else getattr(request.state, "request_id", None) or sanitize_request_id(None)
    )
    token = current_request_id.set(rid)
    try:
        orchestrator = get_orchestrator()
        return await orchestrator.run_text_query(
            query=body.query,
            request_id=rid,
            language=body.language,
            retriever_strategy=body.retriever_strategy,
            top_k=body.top_k,
        )
    finally:
        current_request_id.reset(token)
