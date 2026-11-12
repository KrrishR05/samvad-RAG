"""
SAMVAD Evaluation — Reproducible Experiment Runner

Runs retrieval evaluations on validated EvalDatasets and writes immutable,
machine-readable experiment records:
  - config.json         (experiment parameters + provenance)
  - predictions.jsonl   (per-query retrieved IDs, scores, latency, metrics)
  - summary.json        (aggregate metrics, per-language metrics, latency stats)
  - summary.md          (human-readable benchmark report)
"""

from __future__ import annotations

import json
import platform
import subprocess
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional, Sequence

from pydantic import BaseModel, Field

from app.analytics.percentiles import compute_stats
from app.evaluation.metrics import (
    aggregate_retrieval_metrics,
    evaluate_retrieval_query,
)
from app.evaluation.schemas import DatasetProvenance, EvalDataset
from app.pipeline.interfaces import Retriever
from app.schemas.analytics import PercentileStats


class ExperimentConfig(BaseModel):
    """Configuration for a reproducible retrieval benchmark run."""

    experiment_name: str = Field(..., min_length=1)
    retriever_name: str = Field(..., min_length=1)
    top_k: int = Field(default=10, ge=1)
    k_values: list[int] = Field(default_factory=lambda: [1, 5, 10])
    seed: int = Field(default=42)
    notes: Optional[str] = None
    extra_params: dict[str, Any] = Field(default_factory=dict)


class PerQueryPrediction(BaseModel):
    """Machine-readable per-query output stored in predictions.jsonl."""

    query_id: str
    language: Optional[str] = None
    retrieved_doc_ids: list[str] = Field(default_factory=list)
    scores: list[Optional[float]] = Field(default_factory=list)
    latency_ms: float
    metrics: dict[str, float] = Field(default_factory=dict)
    error: Optional[str] = None


class ExperimentSummary(BaseModel):
    """Full provenance and aggregate results for a completed experiment."""

    experiment_id: str
    git_sha: Optional[str] = None
    timestamp_utc: str
    python_version: str
    platform_info: str
    dataset_provenance: DatasetProvenance
    config: ExperimentConfig
    num_queries: int
    num_errors: int
    overall_metrics: dict[str, float] = Field(default_factory=dict)
    by_language_metrics: dict[str, dict[str, float]] = Field(default_factory=dict)
    latency_stats: Optional[PercentileStats] = None


def _get_git_sha() -> Optional[str]:
    """Return current git HEAD SHA if available, else None."""
    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            stderr=subprocess.DEVNULL,
            text=True,
            timeout=3,
        ).strip()
        return out or None
    except Exception:
        return None


def _generate_experiment_id(name: str) -> str:
    slug = "".join(c if c.isalnum() or c in "-_" else "-" for c in name.lower()).strip("-")
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    short = uuid.uuid4().hex[:8]
    return f"{ts}_{slug or 'exp'}_{short}"


def _render_markdown_report(summary: ExperimentSummary) -> str:
    lines = [
        f"# Experiment Report: `{summary.experiment_id}`",
        "",
        f"- **Timestamp (UTC):** {summary.timestamp_utc}",
        f"- **Git SHA:** `{summary.git_sha or 'unknown'}`",
        f"- **Dataset:** `{summary.dataset_provenance.dataset_id}` "
        f"(split=`{summary.dataset_provenance.split}`, "
        f"type=`{summary.dataset_provenance.source_type.value}`, "
        f"version=`{summary.dataset_provenance.version}`)",
        f"- **Retriever:** `{summary.config.retriever_name}` (top_k={summary.config.top_k})",
        f"- **Queries:** {summary.num_queries} (errors: {summary.num_errors})",
        "",
        "## Overall Retrieval Metrics",
        "",
        "| Metric | Value |",
        "|--------|-------|",
    ]
    for k, v in summary.overall_metrics.items():
        lines.append(f"| `{k}` | {v:.4f} |")

    if summary.by_language_metrics:
        lines.extend(["", "## Per-Language Breakdown", ""])
        for lang, metrics in summary.by_language_metrics.items():
            lines.append(f"### Language: `{lang}`")
            lines.append("")
            lines.append("| Metric | Value |")
            lines.append("|--------|-------|")
            for k, v in metrics.items():
                lines.append(f"| `{k}` | {v:.4f} |")
            lines.append("")

    if summary.latency_stats and summary.latency_stats.count > 0:
        ls = summary.latency_stats
        lines.extend(
            [
                "## Retrieval Latency (ms)",
                "",
                f"- **P50:** {ls.p50} ms",
                f"- **P70:** {ls.p70} ms",
                f"- **P100 (max):** {ls.p100} ms",
                f"- **Mean:** {ls.mean} ms (n={ls.count})",
                "",
            ]
        )

    return "\n".join(lines)


async def run_retrieval_experiment(
    *,
    dataset: EvalDataset,
    retriever: Retriever,
    config: ExperimentConfig,
    output_root: Path,
    experiment_id: Optional[str] = None,
) -> tuple[ExperimentSummary, Path]:
    """
    Execute a reproducible retrieval benchmark and persist immutable artifacts.

    Raises:
        DatasetIntegrityError: If dataset validation fails.
        FileExistsError: If *experiment_id* output directory already exists.
    """
    dataset.validate_integrity()

    exp_id = experiment_id or _generate_experiment_id(config.experiment_name)
    exp_dir = Path(output_root) / exp_id
    if exp_dir.exists():
        raise FileExistsError(
            f"Experiment directory already exists and cannot be overwritten: {exp_dir}"
        )
    exp_dir.mkdir(parents=True, exist_ok=False)

    qrels = dataset.qrels_by_query()
    k_values: Sequence[int] = sorted(set(config.k_values))
    effective_top_k = max(config.top_k, max(k_values))

    predictions: list[PerQueryPrediction] = []
    metric_pairs: list[tuple[str, dict[str, float]]] = []
    latencies: list[float] = []
    num_errors = 0

    for query in dataset.queries:
        t0 = time.perf_counter()
        try:
            candidates = await retriever.retrieve(
                query.text,
                top_k=effective_top_k,
                language=query.language,
            )
            elapsed_ms = (time.perf_counter() - t0) * 1000.0
            latencies.append(elapsed_ms)

            retrieved_ids = [c.chunk_id for c in candidates]
            scores = [c.retrieval_score for c in candidates]
            q_metrics = evaluate_retrieval_query(
                retrieved_ids=retrieved_ids,
                relevance_grades=qrels.get(query.query_id, {}),
                k_values=k_values,
            )
            metric_pairs.append((query.language or "unknown", q_metrics))
            predictions.append(
                PerQueryPrediction(
                    query_id=query.query_id,
                    language=query.language,
                    retrieved_doc_ids=retrieved_ids,
                    scores=scores,
                    latency_ms=round(elapsed_ms, 3),
                    metrics=q_metrics,
                )
            )
        except Exception as exc:
            elapsed_ms = (time.perf_counter() - t0) * 1000.0
            num_errors += 1
            zero_metrics = evaluate_retrieval_query(
                retrieved_ids=[],
                relevance_grades=qrels.get(query.query_id, {}),
                k_values=k_values,
            )
            metric_pairs.append((query.language or "unknown", zero_metrics))
            predictions.append(
                PerQueryPrediction(
                    query_id=query.query_id,
                    language=query.language,
                    latency_ms=round(elapsed_ms, 3),
                    metrics=zero_metrics,
                    error=str(exc),
                )
            )

    overall_metrics, by_lang_metrics = aggregate_retrieval_metrics(metric_pairs)
    summary = ExperimentSummary(
        experiment_id=exp_id,
        git_sha=_get_git_sha(),
        timestamp_utc=datetime.now(timezone.utc).isoformat(),
        python_version=sys.version.split()[0],
        platform_info=platform.platform(),
        dataset_provenance=dataset.provenance,
        config=config,
        num_queries=len(dataset.queries),
        num_errors=num_errors,
        overall_metrics=overall_metrics,
        by_language_metrics=by_lang_metrics,
        latency_stats=compute_stats(latencies) if latencies else None,
    )

    # Persist artifacts
    (exp_dir / "config.json").write_text(
        json.dumps(
            {
                "experiment_id": exp_id,
                "config": config.model_dump(),
                "dataset_provenance": dataset.provenance.model_dump(mode="json"),
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    with (exp_dir / "predictions.jsonl").open("w", encoding="utf-8") as fh:
        for pred in predictions:
            fh.write(pred.model_dump_json() + "\n")

    (exp_dir / "summary.json").write_text(
        summary.model_dump_json(indent=2),
        encoding="utf-8",
    )
    (exp_dir / "summary.md").write_text(
        _render_markdown_report(summary),
        encoding="utf-8",
    )

    return summary, exp_dir

