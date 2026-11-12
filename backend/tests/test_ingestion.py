"""
Tests — Phase 2 Ingestion: Loaders, Normalization, Chunking, DocumentStore
"""

import pytest

from app.core.errors import InputValidationError
from app.ingestion.chunker import chunk_text
from app.ingestion.loaders import load_document_bytes
from app.ingestion.normalizer import normalize_text, sha256_text
from app.ingestion.store import DocumentStatus, DocumentStore
from app.schemas.pipeline import ChunkStrategy


def test_normalize_text_preserves_indic_and_nfc():
    # Decomposed Devanagari vs NFC should normalize identically
    raw = "  गोवा\r\n\r\n\r\nकोंकणी   भारत।  "
    norm = normalize_text(raw)
    assert norm == "गोवा\n\nकोंकणी भारत।"
    assert sha256_text(norm) == sha256_text("गोवा\n\nकोंकणी भारत।")


def test_load_document_bytes_txt_html_and_validation():
    doc = load_document_bytes(
        filename="../../etc/notes.md",
        raw_bytes=b"# SAMVAD\n\nEvidence-grounded RAG.",
        language="en",
    )
    assert doc.filename == "notes.md"  # path traversal stripped
    assert doc.media_type == "text/markdown"
    assert "Evidence-grounded RAG." in doc.content

    html_doc = load_document_bytes(
        filename="page.html",
        raw_bytes=b"<html><script>alert(1)</script><body><h1>Title</h1><p>Body text</p></body></html>",
    )
    assert "alert" not in html_doc.content
    assert "Title" in html_doc.content
    assert "Body text" in html_doc.content

    with pytest.raises(InputValidationError, match="empty"):
        load_document_bytes(filename="a.txt", raw_bytes=b"")

    with pytest.raises(InputValidationError, match="Unsupported"):
        load_document_bytes(filename="malware.exe", raw_bytes=b"MZ")


def test_chunk_strategies_and_provenance():
    text = (
        "Bengaluru is the capital of Karnataka. "
        "गोवा भारत के पश्चिम तट पर स्थित है। "
        "Panaji is the capital of Goa."
    )

    whole = chunk_text(
        text=text,
        parent_document_id="doc-1",
        strategy=ChunkStrategy.WHOLE_PASSAGE,
        language="en",
    )
    assert len(whole) == 1
    assert whole[0].metadata.chunk_index == 0
    assert whole[0].metadata.total_chunks == 1

    sliding = chunk_text(
        text=text,
        parent_document_id="doc-1",
        strategy=ChunkStrategy.SLIDING_WINDOW,
        chunk_size=50,
        chunk_overlap=10,
    )
    assert len(sliding) >= 2
    assert sliding[0].metadata.chunk_strategy == ChunkStrategy.SLIDING_WINDOW
    assert sliding[0].metadata.extra["start_char"] == 0

    semantic = chunk_text(
        text=text,
        parent_document_id="doc-1",
        strategy=ChunkStrategy.SEMANTIC,
        chunk_size=60,
        chunk_overlap=0,
    )
    assert len(semantic) >= 2
    assert any("गोवा" in c.text for c in semantic)


def test_document_store_lifecycle_dedup_and_delete(tmp_path):
    store = DocumentStore(tmp_path / "samvad.db")
    loaded = load_document_bytes(
        filename="goa.txt",
        raw_bytes="Panaji is the capital of Goa.".encode("utf-8"),
        language="en",
    )

    rec1, created1 = store.register_document(
        filename=loaded.filename,
        content_hash=loaded.content_hash,
        media_type=loaded.media_type,
        language=loaded.language,
    )
    assert created1 is True
    assert rec1.status == DocumentStatus.UPLOADED

    # Duplicate content hash returns existing record with created=False
    rec2, created2 = store.register_document(
        filename="goa_copy.txt",
        content_hash=loaded.content_hash,
        media_type=loaded.media_type,
        language=loaded.language,
    )
    assert created2 is False
    assert rec2.doc_id == rec1.doc_id

    chunks = chunk_text(
        text=loaded.content,
        parent_document_id=rec1.doc_id,
        strategy=ChunkStrategy.WHOLE_PASSAGE,
        language="en",
    )
    store.save_chunks(rec1.doc_id, chunks)
    updated = store.get_document(rec1.doc_id)
    assert updated is not None
    assert updated.status == DocumentStatus.PROCESSED
    assert updated.chunk_count == 1

    store.update_status(rec1.doc_id, DocumentStatus.INDEXED)
    assert store.get_document(rec1.doc_id).status == DocumentStatus.INDEXED  # type: ignore[union-attr]
    assert len(store.get_all_chunks()) == 1

    assert store.delete_document(rec1.doc_id) is True
    assert store.get_all_chunks() == []

