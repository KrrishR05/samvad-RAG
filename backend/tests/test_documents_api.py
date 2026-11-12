"""
Tests — Document Upload, Listing, Deletion & Live Pipeline Status API
"""

from __future__ import annotations

from typing import Optional, Sequence

import pytest
from fastapi.testclient import TestClient

from app.analytics.metrics import MetricsStore
from app.core.config import Settings
from app.main import create_app
from app.pipeline.interfaces import GenerationResult, ScoredChunk
from app.pipeline.runtime import SamvadRuntime, set_runtime


class _FakeLLM:
    provider_name = "stub"
    model_name = "stub-llm"

    async def generate(
        self,
        query: str,
        context: Sequence[ScoredChunk],
        language: Optional[str] = None,
    ) -> GenerationResult:
        return GenerationResult(
            answer=f"Based on document: {context[0].text[:40]} [1]",
            grounded=True,
            confidence_score=0.9,
            sources_used=[context[0].chunk_id],
        )


@pytest.fixture
def isolated_client(tmp_path):
    settings = Settings(
        sqlite_db_path=str(tmp_path / "samvad.db"),
        vector_db_path=str(tmp_path / "vec_index"),
        max_document_upload_bytes=1024 * 1024,
    )
    runtime = SamvadRuntime(
        settings=settings,
        metrics_store=MetricsStore(),
        generator=_FakeLLM(),
    )
    set_runtime(runtime)
    app = create_app()
    with TestClient(app) as client:
        yield client
    set_runtime(None)


def test_document_upload_query_and_delete_lifecycle(isolated_client: TestClient):
    # Initial status: LLM configured, 0 indexed docs
    status_resp = isolated_client.get("/api/v1/pipeline/status")
    assert status_resp.status_code == 200
    status_data = status_resp.json()
    assert status_data["retrieval_ready"] is False
    assert status_data["llm_configured"] is True
    assert status_data["llm_model"] == "stub-llm"

    # Upload English markdown document
    content = b"# Bengaluru\nBengaluru is the capital of Karnataka, known for science and technology."
    upload_resp = isolated_client.post(
        "/api/v1/documents",
        files={"file": ("karnataka.md", content, "text/markdown")},
        data={"language": "en", "chunk_strategy": "sliding_window"},
    )
    assert upload_resp.status_code == 200
    up_json = upload_resp.json()
    assert up_json["duplicate"] is False
    assert up_json["document"]["status"] == "indexed"
    assert up_json["total_chunks_indexed"] >= 1
    doc_id = up_json["document"]["doc_id"]

    # Duplicate upload should deduplicate
    dup_resp = isolated_client.post(
        "/api/v1/documents",
        files={"file": ("karnataka_copy.md", content, "text/markdown")},
    )
    assert dup_resp.status_code == 200
    assert dup_resp.json()["duplicate"] is True

    # List documents
    list_resp = isolated_client.get("/api/v1/documents")
    assert list_resp.status_code == 200
    assert list_resp.json()["total_documents"] == 1

    # Query against uploaded document
    q_resp = isolated_client.post(
        "/api/v1/query",
        json={"query": "What is Bengaluru the capital of?", "retriever_strategy": "hybrid"},
    )
    assert q_resp.status_code == 200
    q_json = q_resp.json()
    assert q_json["status"] == "completed"
    assert q_json["grounded"] is True
    assert len(q_json["sources"]) == 1
    assert "[1]" in q_json["answer"]

    # Delete document & verify clean removal
    del_resp = isolated_client.delete(f"/api/v1/documents/{doc_id}")
    assert del_resp.status_code == 200
    assert del_resp.json()["deleted"] is True
    assert del_resp.json()["total_chunks_indexed"] == 0

    missing_del = isolated_client.delete("/api/v1/documents/doc-does-not-exist")
    assert missing_del.status_code == 404


def test_document_upload_rejects_invalid_files(isolated_client: TestClient):
    empty_resp = isolated_client.post(
        "/api/v1/documents",
        files={"file": ("empty.txt", b"", "text/plain")},
    )
    assert empty_resp.status_code == 400

    bad_ext = isolated_client.post(
        "/api/v1/documents",
        files={"file": ("malware.exe", b"MZ...", "application/octet-stream")},
    )
    assert bad_ext.status_code == 400

