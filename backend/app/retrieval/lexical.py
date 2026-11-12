"""
SAMVAD Retrieval — Lexical (Okapi BM25)

Unicode- and Indic-script-aware Okapi BM25 sparse retriever conforming
to the canonical Retriever protocol.
"""

from __future__ import annotations

import math
import unicodedata
from collections import Counter
from typing import Optional, Sequence

from app.ingestion.chunker import DocumentChunk
from app.pipeline.interfaces import ScoredChunk


def tokenize_unicode(text: str) -> list[str]:
    """
    Tokenize Unicode text while preserving Indic combining marks (matras, virama).

    Python's `re` `\\w+` splits Devanagari words at combining marks (`Mc`/`Mn`)
    like 'ा', 'ि', 'ो', '्'. Grouping `L*`, `M*`, and `N*` categories keeps
    Indic words intact.
    """
    if not text:
        return []
    normalized = unicodedata.normalize("NFC", text).lower()
    tokens: list[str] = []
    current: list[str] = []
    for ch in normalized:
        cat = unicodedata.category(ch)
        if cat[0] in ("L", "M", "N"):
            current.append(ch)
        elif current:
            tokens.append("".join(current))
            current.clear()
    if current:
        tokens.append("".join(current))
    return tokens


class LexicalRetriever:
    """
    In-memory Okapi BM25 retriever built over DocumentChunks.

    Supports language metadata filtering and empty-corpus safety.
    """

    strategy_name = "lexical"

    def __init__(
        self,
        chunks: Sequence[DocumentChunk] = (),
        *,
        k1: float = 1.5,
        b: float = 0.75,
    ) -> None:
        if k1 <= 0:
            raise ValueError("BM25 k1 must be positive.")
        if not (0.0 <= b <= 1.0):
            raise ValueError("BM25 b must be in [0, 1].")

        self.k1 = k1
        self.b = b
        self._chunks: list[DocumentChunk] = []
        self._doc_freqs: list[Counter[str]] = []
        self._doc_lens: list[int] = []
        self._idf: dict[str, float] = {}
        self._avgdl: float = 0.0

        if chunks:
            self.build_index(chunks)

    def build_index(self, chunks: Sequence[DocumentChunk]) -> None:
        """Index (or re-index) a sequence of DocumentChunks for BM25 scoring."""
        self._chunks = list(chunks)
        self._doc_freqs = []
        self._doc_lens = []
        df: Counter[str] = Counter()

        for chunk in self._chunks:
            tokens = tokenize_unicode(chunk.text)
            tf = Counter(tokens)
            self._doc_freqs.append(tf)
            self._doc_lens.append(len(tokens))
            for term in tf:
                df[term] += 1

        n = len(self._chunks)
        self._avgdl = (sum(self._doc_lens) / n) if n > 0 else 0.0
        self._idf = {
            term: math.log(1.0 + (n - freq + 0.5) / (freq + 0.5))
            for term, freq in df.items()
        }

    async def retrieve(
        self,
        query: str,
        top_k: int = 10,
        language: Optional[str] = None,
    ) -> Sequence[ScoredChunk]:
        """Score indexed chunks against *query* using Okapi BM25."""
        if top_k <= 0:
            raise ValueError("top_k must be positive.")
        if not self._chunks:
            return []

        q_tokens = tokenize_unicode(query)
        if not q_tokens:
            return []

        avgdl = self._avgdl if self._avgdl > 0 else 1.0
        scored: list[tuple[float, int]] = []

        for idx, chunk in enumerate(self._chunks):
            if language and chunk.metadata.language and chunk.metadata.language != language:
                continue

            tf_map = self._doc_freqs[idx]
            dl = self._doc_lens[idx]
            score = 0.0
            for term in q_tokens:
                tf = tf_map.get(term, 0)
                if tf == 0:
                    continue
                idf = self._idf.get(term, 0.0)
                denom = tf + self.k1 * (1.0 - self.b + self.b * (dl / avgdl))
                score += idf * ((tf * (self.k1 + 1.0)) / denom)

            if score > 0.0:
                scored.append((score, idx))

        scored.sort(key=lambda item: item[0], reverse=True)
        results: list[ScoredChunk] = []
        for score, idx in scored[:top_k]:
            chunk = self._chunks[idx]
            results.append(
                ScoredChunk(
                    chunk_id=chunk.metadata.chunk_id,
                    text=chunk.text,
                    retrieval_score=round(score, 6),
                    retrieval_method=self.strategy_name,
                    metadata=chunk.metadata,
                )
            )
        return results

    async def health_check(self) -> bool:
        return len(self._chunks) > 0
