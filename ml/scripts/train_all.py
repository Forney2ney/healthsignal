"""Train and evaluate every registered tabular model, then write image-model cards."""
import json
import sys
from pathlib import Path

import _bootstrap  # noqa: F401  (adds ml/src to sys.path)

from healthsignal_ml.imaging import write_image_model_cards
from healthsignal_ml.train_tabular import run_all

if __name__ == "__main__":
    only = sys.argv[1:] or None
    summaries = run_all(only)
    cards = write_image_model_cards()
    out = Path(__file__).resolve().parents[1] / "artifacts" / "summary.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"tabular": summaries, "image_models": list(cards)}, indent=2), encoding="utf-8")
    print("summary ->", out)