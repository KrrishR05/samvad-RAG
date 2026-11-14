"""
SAMVAD Retrieval — Context Builder, Optimization & Compression (Phase 3 & 6)

Optimizes retrieved passages before injection into LLM generation context:
  - Deduplication: Drops near-identical passages based on character/token Jaccard similarity.
  - Sentence-Level Compression: Extracts high-salience sentences matching query semantics (Phase 6 M6.3).
  - Token-Budget Packing: Bounds total context length within a configurable token budget.
  - Context Structure: Formats chunks with explicit provenance headers (doc ID, chunk index).
"""

from __future__ import annotations

import re
from typing import Optional, Sequence

from app.pipeline.interfaces import ScoredChunk


_SENTENCE_SPLIT_REGEX = re.compile(r"(?<=[.!?।॥\n])\s+", re.UNICODE)


def _split_into_sentences(text: str) -> list[str]:
    """Split text into sentences across English and Indic terminators."""
    raw = _SENTENCE_SPLIT_REGEX.split(text.strip())
    return [s.strip() for s in raw if s.strip()]


def compute_token_jaccard(text_a: str, text_b: str) -> float:
    """Compute token Jaccard similarity between two texts."""
    tokens_a = set(re.findall(r"\w+", text_a.lower()))
    tokens_b = set(re.findall(r"\w+", text_b.lower()))
    if not tokens_a or not tokens_b:
        return 0.0
    intersection = len(tokens_a & tokens_b)
    union = len(tokens_a | tokens_b)
    return intersection / union if union > 0 else 0.0


class ContextCompressor:
    """
    Extractive sentence-level context compressor (Phase 6 — M6.3).

    Prunes non-salient peripheral sentences from long candidate passages,
    reducing token count while preserving evidence claims for generation.
    """

    def __init__(
        self,
        *,
        min_sentences_to_compress: int = 3,
        max_sentences_per_chunk: int = 3,
        compression_ratio: float = 0.6,
        min_sentence_chars: int = 10,
    ) -> None:
        self.min_sentences_to_compress = min_sentences_to_compress
        self.max_sentences_per_chunk = max_sentences_per_chunk
        self.compression_ratio = compression_ratio
        self.min_sentence_chars = min_sentence_chars

    def compress_chunk(self, chunk: ScoredChunk, query: str) -> ScoredChunk:
        """Compress a single chunk by retaining only high-salience sentences."""
        sentences = _split_into_sentences(chunk.text)
        if len(sentences) <= self.min_sentences_to_compress:
            return chunk

        q_tokens = set(re.findall(r"\w+", query.lower()))
        if not q_tokens:
            return chunk

        scored_sentences: list[tuple[int, float, str]] = []
        for idx, sent in enumerate(sentences):
            if len(sent) < self.min_sentence_chars:
                continue

            s_tokens = set(re.findall(r"\w+", sent.lower()))
            overlap = len(s_tokens & q_tokens)
            # Bonus for first sentence (topic framing)
            position_bias = 0.5 if idx == 0 else 0.0
            salience = (overlap / (len(s_tokens) ** 0.5) if s_tokens else 0.0) + position_bias

            scored_sentences.append((idx, salience, sent))

        if not scored_sentences:
            return chunk

        # Select top-N highest scoring sentences based on ratio and max cap
        budget = max(1, min(self.max_sentences_per_chunk, int(len(sentences) * self.compression_ratio)))
        scored_sentences.sort(key=lambda item: item[1], reverse=True)
        top_selected = scored_sentences[:budget]

        # Re-sort in original textual order
        top_selected.sort(key=lambda item: item[0])
        compressed_text = " ".join(item[2] for item in top_selected)

        # Update metadata
        meta = chunk.metadata.model_copy() if chunk.metadata else None
        if meta and meta.extra is not None:
            meta.extra["compressed"] = True
            meta.extra["original_length"] = len(chunk.text)
            meta.extra["compressed_length"] = len(compressed_text)

        return ScoredChunk(
            chunk_id=chunk.chunk_id,
            text=compressed_text,
            retrieval_score=chunk.retrieval_score,
            reranker_score=chunk.reranker_score,
            retrieval_method=chunk.retrieval_method,
            metadata=meta,
        )


class ContextOptimizer:
    """
    Deduplicates and packs ScoredChunks into a structured, bounded context window.
    Optionally applies extractive sentence compression (Phase 6 — M6.3).
    """

    def __init__(
        self,
        max_context_tokens: int = 3000,
        dedup_similarity_threshold: float = 0.80,
        enable_compression: bool = False,
    ) -> None:
        self.max_context_tokens = max_context_tokens
        self.dedup_similarity_threshold = dedup_similarity_threshold
        self.enable_compression = enable_compression
        self.compressor = ContextCompressor()

    def optimize(
        self,
        candidates: Sequence[ScoredChunk],
        max_chunks: int = 5,
        query: Optional[str] = None,
    ) -> list[ScoredChunk]:
        """
        Deduplicate candidates, optionally compress sentences, and pack within token budget.
        """
        if not candidates:
            return []

        selected: list[ScoredChunk] = []
        estimated_total_tokens = 0

        for cand in candidates:
            if len(selected) >= max_chunks:
                break

            # 1. Deduplication check against already selected chunks
            is_duplicate = False
            for prev in selected:
                sim = compute_token_jaccard(cand.text, prev.text)
                if sim >= self.dedup_similarity_threshold:
                    is_duplicate = True
                    break

            if is_duplicate:
                continue

            # 2. Optional Context Compression (Phase 6)
            target_cand = cand
            if self.enable_compression and query:
                target_cand = self.compressor.compress_chunk(cand, query)

            # 3. Approximate token count (roughly 4 characters per token for English/Indic)
            cand_tokens = max(1, len(target_cand.text) // 4)
            if estimated_total_tokens + cand_tokens > self.max_context_tokens and selected:
                # Stop if adding this chunk exceeds token budget, but always keep at least 1 chunk
                break

            selected.append(target_cand)
            estimated_total_tokens += cand_tokens

        return selected


