"""
Tests — Evaluation CLI
"""

import json
import subprocess
import sys

from app.evaluation.loader import save_eval_dataset
from app.evaluation.schemas import (
    DatasetProvenance,
    DatasetSourceType,
    EvalDataset,
    EvalDocument,
    EvalQuery,
    RelevanceJudgment,
)


def test_cli_validate_command(tmp_path):
    ds = EvalDataset(
        provenance=DatasetProvenance(
            dataset_id="cli-test-v1",
            source_type=DatasetSourceType.SYNTHETIC,
            languages=["en"],
        ),
        documents=[EvalDocument(doc_id="d1", text="Sample text", language="en")],
        queries=[EvalQuery(query_id="q1", text="Sample query?", language="en")],
        judgments=[RelevanceJudgment(query_id="q1", doc_id="d1", relevance=1)],
    )
    ds_path = tmp_path / "ds.json"
    save_eval_dataset(ds, ds_path)

    proc = subprocess.run(
        [sys.executable, "-m", "app.evaluation.cli", "validate", "--dataset", str(ds_path)],
        capture_output=True,
        text=True,
        check=True,
    )
    payload = json.loads(proc.stdout)
    assert payload["status"] == "valid"
    assert payload["dataset_id"] == "cli-test-v1"
    assert payload["source_type"] == "synthetic"

