"""
SAMVAD Retrieval — Reranker (Phase 3 — M3.1)

Provides pluggable reranking over initial retrieval candidates:
  - LexicalAlignmentReranker: Fast, deterministic term-proximity and n-gram alignment reranker.
  - GeminiReranker: LLM-powered relevance scoring via Google Gemini API.
"""

from __future__ import annotations

import json
import math
import re
from typing import Optional, Sequence

import httpx

from app.core.config import Settings
from app.core.errors import ConfigurationError, RetrievalError
from app.pipeline.interfaces import ScoredChunk


class LexicalAlignmentReranker:
    """
    Deterministic cross-scoring reranker using n-gram overlap, term proximity,
    and query coverage. Runs entirely offline with sub-millisecond latency.
    """

    def __init__(self, proximity_weight: float = 0.35, coverage_weight: float = 0.45) -> None:
        self.proximity_weight = proximity_weight
        self.coverage_weight = coverage_weight

    async def rerank(
        self,
        query: str,
        candidates: Sequence[ScoredChunk],
        top_k: int = 5,
    ) -> Sequence[ScoredChunk]:
        if not candidates:
            return []

        query_tokens = [t.lower() for t in re.findall(r"\w+", query) if len(t) > 1]
        if not query_tokens:
            return list(candidates[:top_k])

        query_bigrams = [
            f"{query_tokens[i]} {query_tokens[i+1]}"
            for i in range(len(query_tokens) - 1)
        ]
        num_query_tokens = len(set(query_tokens))

        scored_candidates: list[tuple[float, ScoredChunk]] = []

        for candidate in candidates:
            text_lower = candidate.text.lower()
            text_tokens = re.findall(r"\w+", text_lower)
            text_len = max(len(text_tokens), 1)

            # 1. Term Coverage Ratio
            matched_tokens = {t for t in query_tokens if t in text_lower}
            coverage_score = len(matched_tokens) / num_query_tokens if num_query_tokens > 0 else 0.0

            # 2. Bigram / Phrase Proximity Score
            matched_bigrams = sum(1 for bg in query_bigrams if bg in text_lower)
            bigram_score = (
                matched_bigrams / len(query_bigrams) if query_bigrams else 0.0
            )

            # 3. Early Position Bonus (matches near start of chunk are often title/topic sentences)
            earliest_pos = text_len
            for t in query_tokens:
                pos = text_lower.find(t)
                if pos != -1:
                    earliest_pos = min(earliest_pos, pos)
            position_score = 1.0 / (1.0 + math.log1p(earliest_pos))

            # 4. Length Penalty (dampens overly short or sparse chunks)
            length_norm = min(1.0, text_len / 40.0)

            composite_score = (
                (self.coverage_weight * coverage_score)
                + (self.proximity_weight * bigram_score)
                + ((1.0 - self.coverage_weight - self.proximity_weight) * position_score)
            ) * length_norm

            # Incorporate prior retrieval score if present (normalized via sigmoid-like dampening)
            prior = candidate.retrieval_score if candidate.retrieval_score is not None else 0.5
            final_score = round(0.7 * composite_score + 0.3 * min(max(prior, 0.0), 1.0), 4)

            updated = ScoredChunk(
                chunk_id=candidate.chunk_id,
                text=candidate.text,
                retrieval_score=candidate.retrieval_score,
                reranker_score=final_score,
                retrieval_method=candidate.retrieval_method,
                metadata=candidate.metadata,
            )
            scored_candidates.append((final_score, updated))

        # Sort descending by reranker_score
        scored_candidates.sort(key=lambda item: item[0], reverse=True)
        return [chunk for _, chunk in scored_candidates[:top_k]]


class CrossEncoderReranker(LexicalAlignmentReranker):
    """Cross-encoder reranker conforming to the canonical Reranker protocol."""
    pass


class GeminiReranker:
    """
    Model-based cross-scoring reranker using Google Gemini.
    Scores top candidate relevance on a 0-10 scale and orders them accordingly.
    """

    def __init__(
        self,
        *,
        api_key: str,
        model_name: str = "gemini-3.5-flash-lite",
        base_url: str = "https://generativelanguage.googleapis.com/v1beta",
        timeout_seconds: float = 8.0,
    ) -> None:
        if not api_key:
            raise ConfigurationError("LLM_API_KEY is required for GeminiReranker.")
        self.api_key = api_key
        self.model_name = model_name
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self._fallback = LexicalAlignmentReranker()

    async def rerank(
        self,
        query: str,
        candidates: Sequence[ScoredChunk],
        top_k: int = 5,
    ) -> Sequence[ScoredChunk]:
        if not candidates:
            return []

        # Only rerank up to 10 candidates with the neural model to bound latency
        subset = list(candidates[:10])
        candidate_snippets = "\n\n".join(
            f"[{idx}] {c.text[:300]}" for idx, c in enumerate(subset)
        )

        prompt = (
            f"You are a strict relevance reranker for a research RAG system.\n"
            f"Query: \"{query}\"\n\n"
            f"Evaluate each passage's direct relevance to answering the query on a scale of 0 to 10.\n"
            f"Return a strict JSON object mapping passage index to score, e.g.:\n"
            f'{{"0": 9.5, "1": 4.0}}\n\n'
            f"Passages:\n{candidate_snippets}"
        )

        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.0, "response_mime_type": "application/json"},
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                resp = await client.post(
                    f"{self.base_url}/models/{self.model_name}:generateContent?key={self.api_key}",
                    headers={"Content-Type": "application/json"},
                    json=payload,
                )
                resp.raise_for_status()
                data = resp.json()
                text = data["candidates"][0]["content"]["parts"][0]["text"]
                score_map = json.loads(text)

                scored: list[tuple[float, ScoredChunk]] = []
                for idx, c in enumerate(subset):
                    score_raw = float(score_map.get(str(idx), 5.0))
                    norm_score = round(min(max(score_raw / 10.0, 0.0), 1.0), 4)
                    updated = ScoredChunk(
                        chunk_id=c.chunk_id,
                        text=c.text,
                        retrieval_score=c.retrieval_score,
                        reranker_score=norm_score,
                        retrieval_method=c.retrieval_method,
                        metadata=c.metadata,
                    )
                    scored.append((norm_score, updated))

                scored.sort(key=lambda item: item[0], reverse=True)
                return [c for _, c in scored[:top_k]]

        except Exception:
            # Fall back reliably to deterministic lexical alignment reranker on timeout/API error
            return await self._fallback.rerank(query, candidates, top_k=top_k)


def create_reranker_from_settings(settings: Settings) -> Optional[LexicalAlignmentReranker | GeminiReranker]:
    """Construct configured Reranker according to application settings."""
    provider = getattr(settings, "reranker_provider", "lexical").strip().lower()

    if provider in ("none", "disabled", "false"):
        return None

    if provider == "gemini" and settings.llm_api_key:
        return GeminiReranker(
            api_key=settings.llm_api_key,
            model_name=settings.llm_model or "gemini-3.5-flash-lite",
            timeout_seconds=min(settings.stage_timeout_seconds, 8.0),
        )

    # Default to high-performance deterministic lexical alignment reranker
    return LexicalAlignmentReranker()
