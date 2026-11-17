"""
SAMVAD Analytics — Metrics Store

Thread-safe, bounded in-memory store for latency records.
Provides aggregation methods using the percentile utilities.

NOTE: This is an in-memory implementation suitable for single-process
development. Phase 2+ will persist records to SQLite.
"""

from __future__ import annotations

import logging
import threading
from collections import deque
from datetime import datetime, timezone
from typing import Optional

from app.analytics.percentiles import compute_stats
from app.schemas.analytics import (
    AnalyticsSummaryResponse,
    LatencyRecord,
    LatencyStatsResponse,
    PercentileStats,
    StageLatencyStats,
)

logger = logging.getLogger("samvad.analytics")

DEFAULT_MAX_RECORDS = 10_000


class MetricsStore:
    """Thread-safe bounded in-memory & database-backed metrics store."""

    def __init__(
        self,
        max_records: int = DEFAULT_MAX_RECORDS,
        *,
        hydrate_from_db: bool = False,
    ) -> None:
        if max_records <= 0:
            raise ValueError("max_records must be positive.")
        self._max_records = max_records
        self._records: deque[LatencyRecord] = deque(maxlen=max_records)
        self._lock = threading.Lock()
        if hydrate_from_db:
            self._load_from_db()

    def _load_from_db(self) -> None:
        """Hydrate recent records from the database on startup."""
        try:
            from app.db.connection import get_db
            db = get_db()
            rows = db.fetch_all(
                "SELECT * FROM analytics_records ORDER BY timestamp DESC LIMIT 50"
            )
            rows.reverse()
            for r in rows:
                self._records.append(
                    LatencyRecord(
                        request_id=r["request_id"],
                        query_id=r.get("query_id") or r["request_id"],
                        timestamp=r["timestamp"],
                        success=bool(r.get("success", 1)),
                        strategy=r.get("strategy"),
                        query_text=r.get("query_text"),
                        chunks_retrieved=r.get("chunks_retrieved"),
                        cached=bool(r.get("cached", 0)),
                        stt_ms=r.get("stt_ms"),
                        query_processing_ms=r.get("query_processing_ms"),
                        embedding_ms=r.get("embedding_ms"),
                        retrieval_ms=r.get("retrieval_ms"),
                        reranking_ms=r.get("reranking_ms"),
                        generation_ms=r.get("generation_ms"),
                        guardrail_ms=r.get("guardrail_ms"),
                        total_ms=r.get("total_ms"),
                    )
                )
        except Exception as exc:
            logger.debug("Database analytics hydration skipped: %s", exc)

    def record(self, entry: LatencyRecord) -> None:
        """Append a latency record in-memory and asynchronously persist to database."""
        with self._lock:
            self._records.append(entry)

        try:
            from app.db.connection import get_db
            db = get_db()
            db.execute(
                """
                INSERT INTO analytics_records (
                    request_id, query_id, timestamp, success, strategy,
                    query_text, chunks_retrieved, cached, stt_ms,
                    query_processing_ms, embedding_ms, retrieval_ms,
                    reranking_ms, generation_ms, guardrail_ms, total_ms
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT (request_id) DO NOTHING;
                """,
                (
                    entry.request_id,
                    entry.query_id or entry.request_id,
                    entry.timestamp or datetime.now(timezone.utc).isoformat(),
                    1 if entry.success else 0,
                    entry.strategy,
                    entry.query_text,
                    entry.chunks_retrieved,
                    1 if entry.cached else 0,
                    entry.stt_ms,
                    entry.query_processing_ms,
                    entry.embedding_ms,
                    entry.retrieval_ms,
                    entry.reranking_ms,
                    entry.generation_ms,
                    entry.guardrail_ms,
                    entry.total_ms,
                ),
            )
        except Exception as exc:
            logger.debug("Database record persistence skipped: %s", exc)

    def clear(self) -> None:
        """Remove all stored latency records."""
        with self._lock:
            self._records.clear()

    @property
    def total_requests(self) -> int:
        with self._lock:
            return len(self._records)

    def get_recent_records(self, limit: int = 50) -> list[LatencyRecord]:
        """Return the most recent latency records, newest first."""
        with self._lock:
            records = list(self._records)
        records.reverse()
        return records[:limit]

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
        _store = MetricsStore(hydrate_from_db=True)
    return _store
