"""Download and validate every registered dataset; write a manifest of actual observed counts."""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import _bootstrap  # noqa: F401  (adds ml/src to sys.path)

from healthsignal_ml.datasets import DATASETS, load_dataset

if __name__ == "__main__":
    manifest = {}
    for key in DATASETS:
        df, target, spec = load_dataset(key)
        manifest[key] = {
            "name": spec.name,
            "rows": int(len(df)),
            "columns": int(df.shape[1] - 1),
            "missing_values_total": int(df.drop(columns=[target]).isna().sum().sum()),
            "positive_rate": round(float(df[target].mean()), 4),
            "verified_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        }
        print(f"[{key}] rows={manifest[key]['rows']} cols={manifest[key]['columns']} "
              f"missing={manifest[key]['missing_values_total']} pos_rate={manifest[key]['positive_rate']}")
    out = Path(__file__).resolve().parents[1] / "data" / "manifest.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print("manifest ->", out)