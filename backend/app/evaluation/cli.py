"""
SAMVAD Evaluation CLI

Usage:
    python -m app.evaluation.cli validate --dataset path/to/dataset.json
    python -m app.evaluation.cli inspect-hf --dataset ai4bharat/MSMARCO-XI --split validation
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from app.evaluation.loader import inspect_records_schema, load_eval_dataset


def _cmd_validate(args: argparse.Namespace) -> int:
    path = Path(args.dataset)
    ds = load_eval_dataset(path, verify_checksum=not args.skip_checksum)
    summary = {
        "status": "valid",
        "dataset_id": ds.provenance.dataset_id,
        "source_type": ds.provenance.source_type.value,
        "version": ds.provenance.version,
        "split": ds.provenance.split,
        "documents": len(ds.documents),
        "queries": len(ds.queries),
        "judgments": len(ds.judgments),
        "languages": ds.provenance.languages,
    }
    print(json.dumps(summary, indent=2))
    return 0


def _cmd_inspect_hf(args: argparse.Namespace) -> int:
    try:
        from datasets import load_dataset  # type: ignore[import-not-found]
    except ImportError:
        print(
            "Error: HuggingFace 'datasets' package is not installed. "
            "Install it to inspect remote HuggingFace datasets.",
            file=sys.stderr,
        )
        return 2

    kwargs: dict = {"split": args.split, "streaming": True}
    if args.config:
        kwargs["name"] = args.config

    stream = load_dataset(args.dataset, **kwargs)
    samples = []
    for i, row in enumerate(stream):
        samples.append(dict(row))
        if i + 1 >= args.sample_size:
            break

    report = {
        "dataset": args.dataset,
        "config": args.config,
        "split": args.split,
        "schema": inspect_records_schema(samples, sample_size=args.sample_size),
    }
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="samvad-eval", description="SAMVAD Evaluation CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    p_val = sub.add_parser("validate", help="Validate an EvalDataset JSON file")
    p_val.add_argument("--dataset", required=True, help="Path to dataset JSON")
    p_val.add_argument("--skip-checksum", action="store_true", help="Skip SHA-256 verification")
    p_val.set_defaults(func=_cmd_validate)

    p_hf = sub.add_parser("inspect-hf", help="Inspect schema of a HuggingFace dataset")
    p_hf.add_argument("--dataset", required=True, help="HuggingFace dataset ID")
    p_hf.add_argument("--config", default=None, help="Optional dataset config/language subset")
    p_hf.add_argument("--split", default="train", help="Dataset split")
    p_hf.add_argument("--sample-size", type=int, default=5, help="Rows to inspect")
    p_hf.set_defaults(func=_cmd_inspect_hf)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())

