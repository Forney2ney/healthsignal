"""Liveness and static-asset smoke tests.

These cover the two paths a deployment depends on before any UI is involved:
the health endpoint (used by uptime probes) and the sample-case asset that
the model forms load to prefill real dataset rows.
"""
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
ML_ARTIFACTS = REPO_ROOT / "ml" / "artifacts"


def test_health_and_health_alias_agree(client):
    api = client.get("/api/health")
    assert api.status_code == 200
    assert api.json()["status"] == "ok"

    # Deployment probes conventionally use "/health"; it must not 404.
    alias = client.get("/health")
    assert alias.status_code == 200
    assert alias.json() == api.json()


def test_sample_cases_served_by_backend_and_mirrored_for_the_frontend(client):
    r = client.get("/sample_cases.json")
    assert r.status_code == 200
    body = r.json()
    assert {"heart", "wdbc", "ckd", "pima", "ilpd"} <= set(body)
    assert body["heart"]["positive"]["age"] is not None

    # The frontend ships its own copy as a static asset (Vite only proxies
    # /api), so the two must stay identical or the UI silently loads nothing.
    public_copy = REPO_ROOT / "frontend" / "public" / "sample_cases.json"
    assert public_copy.exists(), "frontend/public/sample_cases.json is missing"
    assert json.loads(public_copy.read_text(encoding="utf-8")) == body
    assert json.loads((ML_ARTIFACTS / "sample_cases.json").read_text(encoding="utf-8")) == body
