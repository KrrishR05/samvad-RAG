"""
SAMVAD Evaluation — Dataset & Experiment Schemas

Typed models for corpus documents, evaluation queries, relevance judgments
(qrels), dataset provenance, and experiment artifacts.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class DatasetSourceType(str, Enum):
    REAL = "real"
    SYNTHETIC = "synthetic"


class DatasetProvenance(BaseModel):
    """Metadata describing the origin, version, and licensing of an eval dataset."""

    dataset_id: str = Field(..., min_length=1)
    version: str = Field(default="unknown")
    source_type: DatasetSourceType = Field(default=DatasetSourceType.REAL)
    source_url: Optional[str] = None
    license: Optional[str] = None
    split: str = Field(default="dev")
    languages: list[str] = Field(default_factory=list)
    checksum_sha256: Optional[str] = None
    notes: Optional[str] = None


class EvalDocument(BaseModel):
    """A single document/passage in an evaluation corpus."""

    doc_id: str = Field(..., min_length=1)
    text: str = Field(..., min_length=1)
    title: Optional[str] = None
    language: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class EvalQuery(BaseModel):
    """A single evaluation query."""

    query_id: str = Field(..., min_length=1)
    text: str = Field(..., min_length=1)
    language: Optional[str] = None
    query_type: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class RelevanceJudgment(BaseModel):
    """Graded relevance judgment (qrel) mapping a query to a corpus document."""

    query_id: str = Field(..., min_length=1)
    doc_id: str = Field(..., min_length=1)
    relevance: int = Field(default=1, ge=0)


class DatasetIntegrityError(ValueError):
    """Raised when an evaluation dataset fails structural integrity checks."""


class EvalDataset(BaseModel):
    """Complete self-contained evaluation dataset with provenance and integrity checks."""

    provenance: DatasetProvenance
    documents: list[EvalDocument] = Field(default_factory=list)
    queries: list[EvalQuery] = Field(default_factory=list)
    judgments: list[RelevanceJudgment] = Field(default_factory=list)

    def validate_integrity(self) -> None:
        """
        Verify uniqueness of IDs and referential integrity of judgments.

        Raises:
            DatasetIntegrityError: On empty corpus/queries, duplicate IDs,
                or dangling query_id/doc_id references.
        """
        if not self.documents:
            raise DatasetIntegrityError("Evaluation dataset has no documents.")
        if not self.queries:
            raise DatasetIntegrityError("Evaluation dataset has no queries.")

        doc_ids: set[str] = set()
        for doc in self.documents:
            if doc.doc_id in doc_ids:
                raise DatasetIntegrityError(f"Duplicate doc_id: '{doc.doc_id}'.")
            doc_ids.add(doc.doc_id)

        query_ids: set[str] = set()
        for q in self.queries:
            if q.query_id in query_ids:
                raise DatasetIntegrityError(f"Duplicate query_id: '{q.query_id}'.")
            query_ids.add(q.query_id)

        seen_pairs: set[tuple[str, str]] = set()
        for j in self.judgments:
            if j.query_id not in query_ids:
                raise DatasetIntegrityError(
                    f"Judgment references unknown query_id: '{j.query_id}'."
                )
            if j.doc_id not in doc_ids:
                raise DatasetIntegrityError(
                    f"Judgment references unknown doc_id: '{j.doc_id}'."
                )
            pair = (j.query_id, j.doc_id)
            if pair in seen_pairs:
                raise DatasetIntegrityError(
                    f"Duplicate judgment for (query_id='{j.query_id}', doc_id='{j.doc_id}')."
                )
            seen_pairs.add(pair)

    def qrels_by_query(self) -> dict[str, dict[str, int]]:
        """Return mapping query_id -> {doc_id: relevance_grade}."""
        mapping: dict[str, dict[str, int]] = {q.query_id: {} for q in self.queries}
        for j in self.judgments:
            mapping[j.query_id][j.doc_id] = j.relevance
        return mapping

