"""
SAMVAD API — Shareable Chat Session Routes

Allows users to create persistent, public read-only share links for any
research session, backed by PostgreSQL (Supabase).
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.api.routes_documents import get_request_user_id
from app.db.connection import get_db

router = APIRouter(prefix="/api/v1", tags=["share"])


class ShareSessionRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=300)
    turns: list[dict[str, Any]] = Field(..., min_length=1, max_length=100)


class ShareSessionResponse(BaseModel):
    share_id: str
    title: str
    created_at: str


class SharedSessionDetail(BaseModel):
    share_id: str
    title: str
    turns: list[dict[str, Any]]
    created_at: str


@router.post(
    "/share",
    response_model=ShareSessionResponse,
    summary="Create a public shareable link for a chat session",
)
async def create_shared_session(
    body: ShareSessionRequest,
    user_id: str = Depends(get_request_user_id),
) -> ShareSessionResponse:
    db = get_db()
    share_id = f"shr_{uuid.uuid4().hex[:10]}"
    now = datetime.now(timezone.utc).isoformat()
    turns_json = json.dumps(body.turns, ensure_ascii=False)

    db.execute(
        """
        INSERT INTO shared_sessions (share_id, title, turns_json, created_by, created_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        (share_id, body.title.strip(), turns_json, user_id, now),
    )

    return ShareSessionResponse(
        share_id=share_id,
        title=body.title.strip(),
        created_at=now,
    )


@router.get(
    "/share/{share_id}",
    response_model=SharedSessionDetail,
    summary="Fetch a public shared chat session",
)
async def get_shared_session(share_id: str) -> SharedSessionDetail:
    db = get_db()
    row = db.fetch_one(
        "SELECT share_id, title, turns_json, created_at FROM shared_sessions WHERE share_id = ?",
        (share_id,),
    )
    if not row:
        raise HTTPException(status_code=404, detail="Shared session not found.")

    raw_turns = row["turns_json"]
    turns = json.loads(raw_turns) if isinstance(raw_turns, str) else (raw_turns or [])

    return SharedSessionDetail(
        share_id=row["share_id"],
        title=row["title"],
        turns=turns,
        created_at=row["created_at"],
    )

