"""Train, save and fully evaluate every tabular model, then write image-model cards.

The tabular path is delegated to ``run_full_evaluation.py`` so that the artifacts a
reviewer reproduces are exactly the artifacts quoted in the submission: CV-based
selection on the train split, dummy baselines on the same held-out split, separate
false-positive / false-negative counts, subgroup figures and failure records.

Deterministic: seed 42.
"""
import json
import sys
from pathlib import Path

import _bootstrap  # noqa: F401  (adds ml/src to sys.path)
import run_full_evaluation

from healthsignal_ml.datasets import DATASETS
from healthsignal_ml.imaging import write_image_model_cards

if __name__ == "__main__":
    only = sys.argv[1:] or list(DATASETS)
    summaries = run_full_evaluation.run(only)
    cards = write_image_model_cards()
    out = Path(__file__).resolve().parents[1] / "artifacts" / "summary.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps({"tabular": summaries, "image_models": list(cards)}, indent=2),
        encoding="utf-8",
    )
    print("summary ->", out)
