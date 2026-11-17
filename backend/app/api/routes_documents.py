"""
SAMVAD API — Document Management & Live Pipeline Status Routes
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, File, Form, Header, HTTPException, UploadFile
from pydantic import BaseModel, Field

from app.core.errors import InputValidationError, PayloadTooLargeError
from app.ingestion.store import DocumentRecord, DocumentStatus
from app.pipeline.runtime import get_runtime
from app.schemas.pipeline import ChunkStrategy

router = APIRouter(prefix="/api/v1", tags=["documents"])


def get_request_user_id(
    authorization: Optional[str] = Header(None),
    x_user_id: Optional[str] = Header(None, alias="X-User-ID"),
) -> str:
    """Resolve active user ID: Bearer token -> X-User-ID -> guest fallback."""
    if authorization and authorization.startswith("Bearer "):
        token = authorization[7:].strip()
        try:
            from app.core.auth_store import get_auth_store
            store = get_auth_store()
            user = store.get_user_from_token(token)
            if user:
                return user.id
        except Exception:
            pass
    if x_user_id and x_user_id.strip():
        return x_user_id.strip()
    return "guest_anonymous"


class DocumentUploadResponse(BaseModel):
    document: DocumentRecord
    duplicate: bool = False
    total_chunks_indexed: int


class DocumentListResponse(BaseModel):
    documents: list[DocumentRecord] = Field(default_factory=list)
    total_documents: int
    total_chunks: int


class DocumentDeleteResponse(BaseModel):
    doc_id: str
    deleted: bool
    total_chunks_indexed: int


class ChunkItemDTO(BaseModel):
    chunk_id: str
    chunk_index: int
    text: str
    char_count: int
    token_count: int
    language: Optional[str] = None
    strategy: Optional[str] = None


class DocumentChunksResponse(BaseModel):
    doc_id: str
    total_chunks: int
    chunks: list[ChunkItemDTO]


class PipelineStatusResponse(BaseModel):
    retrieval_ready: bool
    indexed_documents: int
    indexed_chunks: int
    available_strategies: list[str]
    embedding_provider: str
    embedding_dimension: int
    llm_configured: bool
    llm_provider: Optional[str] = None
    llm_model: Optional[str] = None
    reranker_configured: bool
    stt_configured: bool
    guardrails_configured: bool


@router.post(
    "/documents",
    response_model=DocumentUploadResponse,
    summary="Upload and index a knowledge-base document",
)
async def upload_document(
    file: UploadFile = File(...),
    language: Optional[str] = Form(default=None),
    chunk_strategy: ChunkStrategy = Form(default=ChunkStrategy.SLIDING_WINDOW),
    chunk_size: int = Form(default=800),
    chunk_overlap: int = Form(default=120),
    user_id: str = Depends(get_request_user_id),
) -> DocumentUploadResponse:
    runtime = get_runtime()
    if not file.filename:
        raise InputValidationError("Uploaded file must include a filename.")

    max_bytes = runtime.settings.max_document_upload_bytes
    raw_bytes = await file.read(max_bytes + 1)
    if len(raw_bytes) > max_bytes:
        raise PayloadTooLargeError(
            f"Uploaded file '{file.filename}' exceeds maximum allowed size of {max_bytes} bytes."
        )
    if not raw_bytes:
        raise InputValidationError("Uploaded file is empty.")

    record, duplicate, total_chunks = await runtime.ingest_document(
        filename=file.filename,
        raw_bytes=raw_bytes,
        language=language.strip() if language and language.strip() else None,
        chunk_strategy=chunk_strategy,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        user_id=user_id,
    )
    return DocumentUploadResponse(
        document=record,
        duplicate=duplicate,
        total_chunks_indexed=total_chunks,
    )


@router.get(
    "/documents",
    response_model=DocumentListResponse,
    summary="List indexed and registered documents",
)
async def list_documents(
    user_id: str = Depends(get_request_user_id),
) -> DocumentListResponse:
    runtime = get_runtime()
    docs = runtime.document_store.list_documents(user_id=user_id)
    total_chunks = sum(doc.chunk_count for doc in docs if doc.status == DocumentStatus.INDEXED)
    return DocumentListResponse(
        documents=docs,
        total_documents=len(docs),
        total_chunks=total_chunks,
    )


@router.delete(
    "/documents/{doc_id}",
    response_model=DocumentDeleteResponse,
    summary="Delete a document and rebuild retrieval indexes",
)
async def delete_document(
    doc_id: str,
    user_id: str = Depends(get_request_user_id),
) -> DocumentDeleteResponse:
    runtime = get_runtime()
    deleted, total_chunks = await runtime.delete_document(doc_id, user_id=user_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Document '{doc_id}' not found.")
    return DocumentDeleteResponse(
        doc_id=doc_id,
        deleted=True,
        total_chunks_indexed=total_chunks,
    )


@router.get(
    "/documents/{doc_id}/chunks",
    response_model=DocumentChunksResponse,
    summary="List all chunks associated with a specific document",
)
async def get_document_chunks(
    doc_id: str,
    user_id: str = Depends(get_request_user_id),
) -> DocumentChunksResponse:
    runtime = get_runtime()
    chunks = runtime.document_store.get_chunks_for_document(doc_id, user_id=user_id)
    return DocumentChunksResponse(
        doc_id=doc_id,
        total_chunks=len(chunks),
        chunks=[
            ChunkItemDTO(
                chunk_id=c.metadata.chunk_id,
                chunk_index=c.metadata.chunk_index,
                text=c.text,
                char_count=c.metadata.char_count,
                token_count=c.metadata.token_count,
                language=c.metadata.language,
                strategy=c.metadata.chunk_strategy.value if c.metadata.chunk_strategy else None,
            )
            for c in chunks
        ],
    )


@router.get(
    "/pipeline/status",
    response_model=PipelineStatusResponse,
    summary="Inspect live configured backend pipeline capabilities",
)
async def get_pipeline_status(
    user_id: str = Depends(get_request_user_id),
) -> PipelineStatusResponse:
    runtime = get_runtime()
    user_docs = runtime.document_store.list_documents(user_id=user_id)
    indexed_docs = sum(1 for doc in user_docs if doc.status == DocumentStatus.INDEXED)
    total_user_chunks = sum(doc.chunk_count for doc in user_docs if doc.status == DocumentStatus.INDEXED)
    orch = runtime.orchestrator
    gen = orch.generator
    return PipelineStatusResponse(
        retrieval_ready=total_user_chunks > 0,
        indexed_documents=indexed_docs,
        indexed_chunks=total_user_chunks,
        available_strategies=sorted(orch.retrievers.keys()),
        embedding_provider=runtime.embedding_provider.model_name,
        embedding_dimension=runtime.embedding_provider.dimension,
        llm_configured=gen is not None,
        llm_provider=getattr(gen, "provider_name", None) if gen else None,
        llm_model=getattr(gen, "model_name", None) if gen else None,
        reranker_configured=orch.reranker is not None,
        stt_configured=orch.speech_service is not None,
        guardrails_configured=any(
            g is not None
            for g in (
                orch.input_guard,
                orch.relevance_guard,
                orch.confidence_guard,
                orch.grounding_guard,
            )
        ),
    )

