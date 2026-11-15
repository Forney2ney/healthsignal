"""Smoke test: registry inference + SHAP, and X-ray inference + Grad-CAM."""
import json
import time

import _bootstrap  # noqa: F401

from healthsignal_ml import imaging, model_registry

if __name__ == "__main__":
    cases = json.loads((model_registry.ARTIFACTS_DIR / "sample_cases.json").read_text())
    h = cases["heart"]["positive"]
    t0 = time.time()
    r = model_registry.predict("heart", h)
    print(f"Heart positive-case score: {r['probability']:.4f} (pred={r['prediction']}) in {time.time()-t0:.2f}s")
    print("  explanation:", (r.get('explanation') or {}).get('method'), (r.get('explanation') or {}).get('top_features', [])[:3])
    neg = cases["heart"]["negative"]
    print(f"Heart negative-case score: {model_registry.predict('heart', neg)['probability']:.4f}")
    for k in ("pima", "ckd", "ilpd", "wdbc"):
        rr = model_registry.predict(k, cases[k]["positive"])
        print(f"{k} score: {rr['probability']:.4f} (expected source label=1)")

    print("\nImage models:")
    print(imaging.imaging_status())
    from pathlib import Path

    sample = Path(__file__).resolve().parents[2] / "backend" / "assets" / "samples" / "00000001_000.png"
    if sample.exists():
        res = imaging.analyze_image(sample, "cxr_nih")
        print("cxr_nih top:", sorted(res["probabilities"].items(), key=lambda kv: -kv[1])[:3], res["inference_ms"], "ms")
        print("  gradcam present:", "gradcam" in res)
    else:
        print("sample image not found; skipped (fetch_samples.py first)")