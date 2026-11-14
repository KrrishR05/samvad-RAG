"""
SAMVAD Guardrails — Phase 4: Trustworthy Generation & Security Hardening

Production implementations matching the canonical GuardrailService protocol:
- InputGuard: Query validation, null-byte filtering, and prompt injection isolation (M4.1).
- ConfidenceGuard: Calibrated retrieval/reranker score thresholding to prevent hallucination (M4.2).
- RelevanceGuard: Query-context topical lexical alignment checking (M4.2).
- GroundingGuard: Citation existence, index bounds verification, and claim-level grounding (M4.2).
"""

from __future__ import annotations

import re
from typing import Optional, Sequence

from app.pipeline.interfaces import GuardrailResult, ScoredChunk

_CITATION_RE = re.compile(r"\[(\d+)\]")

# Common multilingual/English/Indic stopwords for substantive keyword filtering
_STOPWORDS = {
    "the", "is", "at", "which", "on", "and", "a", "an", "in", "to", "for", "of", "or",
    "what", "who", "where", "how", "this", "that", "it", "with", "as", "by", "from",
    "be", "are", "was", "were", "been", "have", "has", "had", "do", "does", "did",
    "का", "के", "की", "है", "हैं", "में", "पर", "और", "से", "को", "या", "क्या",
    "बताओ", "दीजिए", "गई", "गया", "था", "थी", "थे", "एक", "यह", "वह", "इस", "उस"
}


def _extract_content_words(text: str) -> set[str]:
    """Extract substantive lowercased words with length >= 2, excluding stopwords."""
    tokens = re.findall(r"\w+", text.lower(), re.UNICODE)
    return {t for t in tokens if len(t) >= 2 and t not in _STOPWORDS}


class InputGuard:
    """
    Validates user queries before pipeline retrieval.
    Enforces quality, character safety, length bounds, and prompt injection defense (M4.1).
    """

    guardrail_name = "input_guard"

    INJECTION_PATTERNS = [
        re.compile(
            r"\b(?:ignore|disregard|forget|override)\s+(?:all\s+)?(?:previous|prior|above)\s+(?:instructions|directives|rules|prompts|system)\b",
            re.IGNORECASE,
        ),
        re.compile(
            r"\b(?:system\s+override|jailbreak\s+mode|developer\s+mode\s+enabled|dan\s+mode|unfiltered\s+mode)\b",
            re.IGNORECASE,
        ),
        re.compile(
            r"\b(?:reveal|print|show|output|leak)\s+(?:your\s+)?(?:system\s+prompt|initial\s+instructions|system\s+instructions|secret\s+key|api_key)\b",
            re.IGNORECASE,
        ),
        re.compile(
            r"\b(?:act\s+as\s+an\s+unfiltered|bypass\s+all\s+(?:filters|restrictions|guardrails|safety))\b",
            re.IGNORECASE,
        ),
        re.compile(
            r"</(?:evidence|context|system|prompt)>|<(?:im_start|im_end)>|<\|(?:endoftext|im_start|im_end)\|>",
            re.IGNORECASE,
        ),
    ]

    def __init__(self, max_length: int = 2500) -> None:
        self.max_length = max_length

    async def check(
        self,
        query: Optional[str] = None,
        *,
        answer: Optional[str] = None,
        context: Optional[Sequence[ScoredChunk]] = None,
        confidence: Optional[float] = None,
        **kwargs,
    ) -> GuardrailResult:
        if query is None or len(query.strip()) == 0:
            return GuardrailResult(
                passed=False,
                reason="Empty or whitespace-only query.",
                action="abstain",
            )
        if "\x00" in query:
            return GuardrailResult(
                passed=False,
                reason="Query contains invalid null-byte characters.",
                action="abstain",
            )
        if len(query) > self.max_length:
            return GuardrailResult(
                passed=False,
                reason=f"Query exceeds maximum allowed length of {self.max_length} characters.",
                action="abstain",
            )
        for pattern in self.INJECTION_PATTERNS:
            if pattern.search(query):
                return GuardrailResult(
                    passed=False,
                    reason="Query rejected: prompt injection, delimiter override, or adversarial instruction pattern detected.",
                    action="abstain",
                )
        return GuardrailResult(passed=True)


class RelevanceGuard:
    """
    Checks topical alignment between query content tokens and retrieved context chunks (M4.2).
    Abstains early when retrieval produces unrelated noise.
    """

    guardrail_name = "relevance_guard"

    def __init__(self, min_overlap_ratio: float = 0.05) -> None:
        self.min_overlap_ratio = min_overlap_ratio

    async def check(
        self,
        query: Optional[str] = None,
        *,
        answer: Optional[str] = None,
        context: Optional[Sequence[ScoredChunk]] = None,
        confidence: Optional[float] = None,
        **kwargs,
    ) -> GuardrailResult:
        if not query:
            return GuardrailResult(passed=True)
        if not context:
            return GuardrailResult(
                passed=False,
                reason="No context chunks provided for relevance evaluation.",
                action="abstain",
            )

        q_tokens = _extract_content_words(query)
        if not q_tokens:
            return GuardrailResult(passed=True)

        context_text = " ".join(c.text for c in context)
        c_tokens = _extract_content_words(context_text)

        overlap = q_tokens.intersection(c_tokens)
        overlap_ratio = len(overlap) / len(q_tokens)

        if overlap_ratio < self.min_overlap_ratio:
            return GuardrailResult(
                passed=False,
                reason=(
                    f"Context relevance overlap ({overlap_ratio:.1%}) is below threshold "
                    f"({self.min_overlap_ratio:.1%}). No substantive query terms match indexed context."
                ),
                action="abstain",
            )

        return GuardrailResult(passed=True)


class ConfidenceGuard:
    """
    Pre-generation guardrail.
    Evaluates retrieval/reranking scores against a calibrated confidence threshold (M4.2).
    Prevents hallucination and wasteful LLM generation when evidence is missing or weak.
    """

    guardrail_name = "confidence_guard"

    def __init__(self, min_confidence_score: float = 0.15) -> None:
        self.min_confidence_score = min_confidence_score

    async def check(
        self,
        query: Optional[str] = None,
        *,
        answer: Optional[str] = None,
        context: Optional[Sequence[ScoredChunk]] = None,
        confidence: Optional[float] = None,
        **kwargs,
    ) -> GuardrailResult:
        if not context:
            return GuardrailResult(
                passed=False,
                reason="No context chunks available for confidence check.",
                action="abstain",
            )

        # Check explicit confidence float if provided
        if confidence is not None:
            if confidence < self.min_confidence_score:
                return GuardrailResult(
                    passed=False,
                    reason=f"Pipeline confidence ({confidence:.2f}) below threshold ({self.min_confidence_score:.2f}).",
                    action="abstain",
                )
            return GuardrailResult(passed=True)

        # Evaluate candidate chunk scores
        scores: list[float] = []
        for c in context:
            if c.reranker_score is not None:
                scores.append(c.reranker_score)
            elif c.retrieval_score is not None:
                scores.append(c.retrieval_score)

        if not scores:
            return GuardrailResult(
                passed=False,
                reason="Context chunks contain no retrieval or reranking scores.",
                action="abstain",
            )

        max_score = max(scores)
        if max_score < self.min_confidence_score:
            return GuardrailResult(
                passed=False,
                reason=(
                    f"Top retrieved candidate score ({max_score:.2f}) is below confidence "
                    f"threshold ({self.min_confidence_score:.2f}). Insufficient evidence to answer reliably."
                ),
                action="abstain",
            )

        return GuardrailResult(passed=True)


class GroundingGuard:
    """
    Post-generation guardrail.
    Verifies that:
    1. Every cited bracket [k] references a valid context chunk index (1 <= k <= len(context)).
    2. Zero phantom / fabricated citations exist (M4.2).
    3. The generated answer has real citation backing when context is provided.
    4. Citing claims have verifiable substantive overlap with the cited context chunk.
    """

    guardrail_name = "grounding_guard"

    def __init__(
        self,
        enforce_citation_presence: bool = True,
        min_claim_overlap: int = 1,
    ) -> None:
        self.enforce_citation_presence = enforce_citation_presence
        self.min_claim_overlap = min_claim_overlap

    async def check(
        self,
        query: Optional[str] = None,
        *,
        answer: Optional[str] = None,
        context: Optional[Sequence[ScoredChunk]] = None,
        confidence: Optional[float] = None,
        **kwargs,
    ) -> GuardrailResult:
        if not answer or not answer.strip():
            return GuardrailResult(
                passed=False,
                reason="Generated answer is empty.",
                action="abstain",
            )

        if not context:
            return GuardrailResult(
                passed=False,
                reason="No context chunks provided for grounding check.",
                action="abstain",
            )

        total_chunks = len(context)
        citations = [int(m.group(1)) for m in _CITATION_RE.finditer(answer)]

        if not citations:
            if self.enforce_citation_presence:
                return GuardrailResult(
                    passed=False,
                    reason="Answer contains zero citations to provided context evidence.",
                    action="abstain",
                )
            return GuardrailResult(passed=True)

        # 1. Existence / Range validation: check for fabricated indices
        out_of_bounds = [c for c in citations if c < 1 or c > total_chunks]
        if out_of_bounds:
            return GuardrailResult(
                passed=False,
                reason=(
                    f"Fabricated citation index detected: answer cites {out_of_bounds}, "
                    f"but only {total_chunks} context passages were provided."
                ),
                action="abstain",
            )

        # 2. Content alignment verification
        sentences = re.split(r"(?<=[.!?।॥\n])\s+", answer)
        for s in sentences:
            s_cits = [int(m.group(1)) for m in _CITATION_RE.finditer(s)]
            if not s_cits:
                continue
            s_words = _extract_content_words(s)
            if not s_words:
                continue
            for cit in s_cits:
                chunk = context[cit - 1]
                chunk_words = _extract_content_words(chunk.text)
                shared = s_words.intersection(chunk_words)
                if len(shared) < self.min_claim_overlap:
                    return GuardrailResult(
                        passed=False,
                        reason=(
                            f"Citation [{cit}] failed grounding verification: cited claim contains "
                            f"no shared substantive terms with source chunk '{chunk.chunk_id}'."
                        ),
                        action="abstain",
                    )

        return GuardrailResult(passed=True)
