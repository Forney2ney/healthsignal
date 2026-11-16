"""Pick representative PUBLIC dataset records to prefill the demo UI.

Each example is a real de-identified row from the model's own source dataset,
labelled by its true dataset label so the UI can compare the model output with
the source label. No patient data is invented; nothing here represents a real
living patient, and rows are clearly labelled as dataset records in the UI.
"""
import json
from pathlib import Path

import _bootstrap  # noqa: F401

import numpy as np
import pandas as pd

from healthsignal_ml.datasets import DATASETS, load_dataset
from healthsignal_ml.model_registry import FEATURE_META

if __name__ == "__main__":
    out: dict[str, dict] = {}
    for key in DATASETS:
        df, target, spec = load_dataset(key)
        meta = FEATURE_META[key]
        cols = [c for c in meta if c in df.columns]
        sub = df[cols + [target]].copy()

        def pick(label: int) -> dict:
            pool = sub[sub[target] == label]
            if pool.empty:
                return {}
            num = pool[cols].apply(pd.to_numeric, errors="coerce")
            med = num.median()
            dist = num.sub(med).abs().sum(axis=1, skipna=True)
            i = int(np.argmin(dist.to_numpy()))
            row = pool.iloc[i][cols]
            return {c: (None if pd.isna(row[c]) else
                        (float(row[c]) if isinstance(row[c], (int, float, np.floating, np.integer)) else str(row[c])))
                    for c in cols}

        out[key] = {"positive": pick(1), "negative": pick(0)}
        print(f"[{key}] positives={int((df[target] == 1).sum())} negatives={int((df[target] == 0).sum())}")
    payload = json.dumps(out, indent=2)
    dest = Path(__file__).resolve().parents[1] / "artifacts" / "sample_cases.json"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(payload, encoding="utf-8")
    print("sample cases ->", dest)

    # The web UI loads this file as a static asset, so keep a copy in the
    # frontend's public/ directory in sync with the ML artifact.
    web_dest = Path(__file__).resolve().parents[2] / "frontend" / "public" / "sample_cases.json"
    web_dest.parent.mkdir(parents=True, exist_ok=True)
    web_dest.write_text(payload, encoding="utf-8")
    print("sample cases ->", web_dest)