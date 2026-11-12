"""
SAMVAD Ingestion — Configurable Multi-Strategy Chunker

Implements all four ChunkStrategy variants with character-offset provenance
and Indic-aware sentence splitting (supports Devanagari danda '।' alongside '.!?').
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional

from app.schemas.pipeline import ChunkMetadata, ChunkStrategy

_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?।॥])\s+|\n{2,}")


@dataclass
class DocumentChunk:
    """A single chunk with text and full ChunkMetadata provenance."""

    text: str
    metadata: ChunkMetadata


def _approx_token_count(text: str) -> int:
    return len(text.split())


def _chunk_spans_fixed(length: int, size: int, overlap: int) -> list[tuple[int, int]]:
    spans: list[tuple[int, int]] = []
    start = 0
    step = size - overlap
    while start < length:
        end = min(start + size, length)
        spans.append((start, end))
        if end >= length:
            break
        start += step
    return spans


def chunk_text(
    *,
    text: str,
    parent_document_id: str,
    strategy: ChunkStrategy = ChunkStrategy.SLIDING_WINDOW,
    chunk_size: int = 800,
    chunk_overlap: int = 120,
    language: Optional[str] = None,
) -> list[DocumentChunk]:
    """
    Segment normalized text into DocumentChunks using the requested ChunkStrategy.

    Args:
        text: Normalized document text.
        parent_document_id: Source document ID for provenance.
        strategy: ChunkStrategy enum value.
        chunk_size: Target maximum characters per chunk (must be > 0).
        chunk_overlap: Character overlap for sliding_window (0 <= overlap < chunk_size).
        language: Optional ISO 639-1 language code.
    """
    cleaned = text.strip()
    if not cleaned:
        return []
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive.")
    if chunk_overlap < 0 or chunk_overlap >= chunk_size:
        raise ValueError("chunk_overlap must satisfy 0 <= chunk_overlap < chunk_size.")

    raw_segments: list[tuple[str, int, int]] = []

    if strategy == ChunkStrategy.WHOLE_PASSAGE:
        raw_segments.append((cleaned, 0, len(cleaned)))

    elif strategy == ChunkStrategy.FIXED_SIZE:
        for start, end in _chunk_spans_fixed(len(cleaned), chunk_size, overlap=0):
            seg = cleaned[start:end].strip()
            if seg:
                raw_segments.append((seg, start, end))

    elif strategy == ChunkStrategy.SLIDING_WINDOW:
        for start, end in _chunk_spans_fixed(len(cleaned), chunk_size, overlap=chunk_overlap):
            seg = cleaned[start:end].strip()
            if seg:
                raw_segments.append((seg, start, end))

    elif strategy == ChunkStrategy.SEMANTIC:
        units = [u.strip() for u in _SENTENCE_SPLIT_RE.split(cleaned) if u.strip()]
        current: list[str] = []
        current_len = 0
        cursor = 0
        chunk_start = 0

        for unit in units:
            unit_pos = cleaned.find(unit, cursor)
            if unit_pos == -1:
                unit_pos = cursor
            if not current:
                chunk_start = unit_pos

            projected = current_len + (1 if current else 0) + len(unit)
            if current and projected > chunk_size:
                seg = " ".join(current)
                raw_segments.append((seg, chunk_start, cursor))
                current = [unit]
                current_len = len(unit)
                chunk_start = unit_pos
            else:
                current.append(unit)
                current_len = projected
            cursor = unit_pos + len(unit)

        if current:
            seg = " ".join(current)
            raw_segments.append((seg, chunk_start, cursor))

    total = len(raw_segments)
    chunks: list[DocumentChunk] = []
    for idx, (seg_text, start_char, end_char) in enumerate(raw_segments):
        chunk_id = f"{parent_document_id}::chunk_{idx}"
        meta = ChunkMetadata(
            chunk_id=chunk_id,
            parent_document_id=parent_document_id,
            language=language,
            chunk_strategy=strategy,
            chunk_index=idx,
            total_chunks=total,
            char_count=len(seg_text),
            token_count=_approx_token_count(seg_text),
            extra={
                "start_char": start_char,
                "end_char": end_char,
            },
        )
        chunks.append(DocumentChunk(text=seg_text, metadata=meta))

    return chunks

