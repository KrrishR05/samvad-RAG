"""
SAMVAD Request Schemas

All inbound request models for the SAMVAD API.
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class ConversationTurn(BaseModel):
    """A single prior user/assistant exchange for multi-turn conversational context."""

    query: str = Field(..., min_length=1, max_length=2000)
    answer: Optional[str] = Field(default=None, max_length=16000)


class QueryRequest(BaseModel):
    """Text-based query request."""

    query: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="The user's natural-language question.",
    )
    request_id: Optional[str] = Field(
        default=None,
        description="Client-provided request ID. Server generates one if absent.",
    )
    language: Optional[str] = Field(
        default=None,
        description="ISO 639-1 language code hint (e.g. 'en', 'hi', 'ta').",
    )
    retriever_strategy: Optional[str] = Field(
        default=None,
        description="Optional retriever strategy override: 'hybrid', 'dense', or 'lexical'.",
    )
    top_k: Optional[int] = Field(
        default=None,
        ge=1,
        le=50,
        description="Optional number of chunks to retrieve (overrides server default).",
    )
    history: list[ConversationTurn] = Field(
        default_factory=list,
        max_length=50,
        description="Prior conversation turns in the current session for resolving follow-up questions.",
    )


class VoiceQueryRequest(BaseModel):
    """
    Metadata accompanying a voice query.

    The actual audio binary is received as a multipart file upload;
    this model carries the associated metadata fields.
    """

    request_id: Optional[str] = Field(
        default=None,
        description="Client-provided request ID. Server generates one if absent.",
    )
    language: Optional[str] = Field(
        default=None,
        description="ISO 639-1 language code hint for the STT provider.",
    )
