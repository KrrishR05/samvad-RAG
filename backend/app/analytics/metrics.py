"""
SAMVAD Analytics — Metrics Store

Thread-safe, bounded in-memory store for latency records.
Provides aggregation methods using the percentile utilities.

NOTE: This is an in-memory implementation suitable for single-process
development. Phase 2+ will persist records to SQLite.
"""

from __future__ import annotations

import threading
from collections import deque
from typing import Optional

from app.analytics.percentiles import compute_stats
from app.schemas.analytics import (
    AnalyticsSummaryResponse,
    LatencyRecord,
    LatencyStatsResponse,
    PercentileStats,
    StageLatencyStats,
)

DEFAULT_MAX_RECORDS = 10_000


class MetricsStore:
    """Thread-safe bounded in-memory metrics store."""

    def __init__(self, max_records: int = DEFAULT_MAX_RECORDS) -> None:
        if max_records <= 0:
            raise ValueError("max_records must be positive.")
        self._max_records = max_records
        self._records: deque[LatencyRecord] = deque(maxlen=max_records)
        self._lock = threading.Lock()

    def record(self, entry: LatencyRecord) -> None:
        """Append a latency record (evicting oldest if at capacity)."""
        with self._lock:
            self._records.append(entry)

    def clear(self) -> None:
        """Remove all stored latency records."""
        with self._lock:
            self._records.clear()

    @property
    def total_requests(self) -> int:
        with self._lock:
            return len(self._records)

    def get_summary(self) -> AnalyticsSummaryResponse:
        """Compute an analytics summary across all recorded requests."""
        with self._lock:
            records = list(self._records)

        if not records:
            return AnalyticsSummaryResponse(
                total_requests=0,
                message="No benchmark data available. Run pipeline queries to collect latency metrics.",
            )

        return AnalyticsSummaryResponse(
            total_requests=len(records),
            stage_latency=self._compute_stage_stats(records),
        )

    def get_latency_stats(self) -> LatencyStatsResponse:
        """Compute detailed latency statistics."""
        with self._lock:
            records = list(self._records)

        if not records:
            return LatencyStatsResponse(
                total_records=0,
                message="No latency data recorded yet.",
            )

        total_values = [r.total_ms for r in records if r.total_ms is not None]

        return LatencyStatsResponse(
            total_records=len(records),
            overall=compute_stats(total_values) if total_values else None,
            by_stage=self._compute_stage_stats(records),
        )

    @staticmethod
    def _compute_stage_stats(records: list[LatencyRecord]) -> StageLatencyStats:
        """Extract per-stage values and compute stats."""

        def _extract(attr: str) -> Optional[PercentileStats]:
            vals = [getattr(r, attr) for r in records if getattr(r, attr) is not None]
            return compute_stats(vals) if vals else None

        return StageLatencyStats(
            stt=_extract("stt_ms"),
            query_processing=_extract("query_processing_ms"),
            embedding=_extract("embedding_ms"),
            retrieval=_extract("retrieval_ms"),
            reranking=_extract("reranking_ms"),
            generation=_extract("generation_ms"),
            guardrail=_extract("guardrail_ms"),
            total=_extract("total_ms"),
        )


# Singleton
_store: Optional[MetricsStore] = None


def get_metrics_store() -> MetricsStore:
    global _store
    if _store is None:
        _store = MetricsStore()
    return _store
