"""
SAMVAD API — Query Routes

Text-based query endpoint.
"""

from __future__ import annotations

import json
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

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


@router.post(
    "/query/stream",
    summary="Submit a query with Server-Sent Events (SSE) stage-by-stage streaming",
)
async def stream_query(request: Request, body: QueryRequest) -> StreamingResponse:
    """
    Stream query pipeline execution progress in real time via Server-Sent Events (SSE) (Phase 5 — M5.3).
    Emits stage_start, stage_complete, and final complete response events.
    """
    rid = (
        sanitize_request_id(body.request_id)
        if body.request_id
        else getattr(request.state, "request_id", None) or sanitize_request_id(None)
    )

    async def event_generator():
        token = current_request_id.set(rid)
        try:
            orchestrator = get_orchestrator()
            async for evt in orchestrator.stream_text_query(
                query=body.query,
                request_id=rid,
                language=body.language,
                retriever_strategy=body.retriever_strategy,
                top_k=body.top_k,
            ):
                event_name = evt.get("event", "message")
                data_str = json.dumps(evt, ensure_ascii=False)
                yield f"event: {event_name}\ndata: {data_str}\n\n"
        finally:
            current_request_id.reset(token)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Request-ID": rid,
        },
    )
