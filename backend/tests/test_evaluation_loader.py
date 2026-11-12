"""
Tests — Evaluation Dataset Loader & Checksum Verification
"""

import json
import pytest

from app.evaluation.loader import (
    compute_dataset_content_sha256,
    inspect_records_schema,
    load_eval_dataset,
    save_eval_dataset,
)
from app.evaluation.schemas import (
    DatasetIntegrityError,
    DatasetProvenance,
    DatasetSourceType,
    EvalDataset,
    EvalDocument,
    EvalQuery,
    RelevanceJudgment,
)


def _make_dataset() -> EvalDataset:
    return EvalDataset(
        provenance=DatasetProvenance(
            dataset_id="smoke-v1",
            version="1.0.0",
            source_type=DatasetSourceType.SYNTHETIC,
            languages=["en", "hi"],
        ),
        documents=[
            EvalDocument(doc_id="d1", text="Goa is on the west coast of India.", language="en"),
            EvalDocument(doc_id="d2", text="कोंकणी गोवा की राजभाषा है।", language="hi"),
        ],
        queries=[
            EvalQuery(query_id="q1", text="Where is Goa located?", language="en"),
        ],
        judgments=[
            RelevanceJudgment(query_id="q1", doc_id="d1", relevance=1),
        ],
    )


def test_save_and_load_eval_dataset_with_checksum(tmp_path):
    ds = _make_dataset()
    out = tmp_path / "dataset.json"
    digest = save_eval_dataset(ds, out)

    loaded = load_eval_dataset(out)
    assert loaded.provenance.checksum_sha256 == digest
    assert compute_dataset_content_sha256(loaded) == digest
    assert len(loaded.documents) == 2


def test_load_eval_dataset_detects_tampered_content(tmp_path):
    ds = _make_dataset()
    out = tmp_path / "dataset.json"
    save_eval_dataset(ds, out)

    raw = json.loads(out.read_text(encoding="utf-8"))
    raw["documents"][0]["text"] = "Tampered text."
    out.write_text(json.dumps(raw), encoding="utf-8")

    with pytest.raises(DatasetIntegrityError, match="checksum mismatch"):
        load_eval_dataset(out)


def test_inspect_records_schema():
    schema = inspect_records_schema(
        [
            {"query_id": "1", "query": "hello", "pos": ["a"]},
            {"query_id": "2", "query": None, "pos": ["b"]},
        ]
    )
    assert schema["count_inspected"] == 2
    assert schema["fields"]["query"] == ["NoneType", "str"]
    assert schema["fields"]["pos"] == ["list"]

