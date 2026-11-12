"""
SAMVAD Evaluation — Dataset Loader, Checksum & Integrity Verification

Loads and validates EvalDataset artifacts from disk with deterministic
SHA-256 content-checksum verification and schema inspection utilities
for external datasets (e.g. AI4Bharat MSMARCO-XI).
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from app.evaluation.schemas import DatasetIntegrityError, EvalDataset


def compute_file_sha256(path: Path) -> str:
    """Compute hex SHA-256 digest of a file."""
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def compute_dataset_content_sha256(dataset: EvalDataset) -> str:
    """
    Compute a deterministic SHA-256 digest over dataset documents, queries,
    and relevance judgments (independent of provenance metadata edits).
    """
    canonical_payload = json.dumps(
        {
            "documents": [d.model_dump(mode="json") for d in dataset.documents],
            "queries": [q.model_dump(mode="json") for q in dataset.queries],
            "judgments": [j.model_dump(mode="json") for j in dataset.judgments],
        },
        sort_keys=True,
        ensure_ascii=False,
    ).encode("utf-8")
    return hashlib.sha256(canonical_payload).hexdigest()


def save_eval_dataset(dataset: EvalDataset, path: Path) -> str:
    """
    Validate, stamp content SHA-256 into provenance, and write an EvalDataset to JSON.

    Returns the computed content SHA-256 digest.
    """
    dataset.validate_integrity()
    digest = compute_dataset_content_sha256(dataset)
    stamped = dataset.model_copy(
        update={
            "provenance": dataset.provenance.model_copy(
                update={"checksum_sha256": digest}
            )
        }
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(stamped.model_dump_json(indent=2), encoding="utf-8")
    return digest


def load_eval_dataset(
    path: Path,
    *,
    verify_checksum: bool = True,
) -> EvalDataset:
    """
    Load an EvalDataset from JSON, verify its content SHA-256 checksum (if present),
    and run full structural integrity validation.
    """
    if not path.exists():
        raise FileNotFoundError(f"Evaluation dataset not found: {path}")

    raw = json.loads(path.read_text(encoding="utf-8"))
    dataset = EvalDataset.model_validate(raw)
    dataset.validate_integrity()

    if verify_checksum and dataset.provenance.checksum_sha256:
        actual = compute_dataset_content_sha256(dataset)
        if actual != dataset.provenance.checksum_sha256:
            raise DatasetIntegrityError(
                f"Content checksum mismatch for {path}: "
                f"expected {dataset.provenance.checksum_sha256}, got {actual}."
            )

    return dataset


def inspect_records_schema(records: list[dict[str, Any]], sample_size: int = 5) -> dict[str, Any]:
    """
    Inspect field names and observed Python types across a sample of raw records.

    Used to verify external dataset schemas (such as MSMARCO-XI) before
    writing normalization adapters.
    """
    if not records:
        return {"count_inspected": 0, "fields": {}}

    sample = records[:sample_size]
    field_types: dict[str, set[str]] = {}
    for rec in sample:
        for key, val in rec.items():
            field_types.setdefault(key, set()).add(type(val).__name__)

    return {
        "count_inspected": len(sample),
        "fields": {k: sorted(v) for k, v in sorted(field_types.items())},
    }
