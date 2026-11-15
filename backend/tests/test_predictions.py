import json
from pathlib import Path

import pytest

ML_ARTIFACTS = Path(__file__).resolve().parents[2] / "ml" / "artifacts"


def test_models_endpoint_lists_all_models(client):
    r = client.get("/api/models")
    assert r.status_code == 200
    keys = {m["model_key"] for m in r.json()["models"]}
    assert {"heart", "wdbc", "ckd", "pima", "ilpd"} <= keys
    for m in r.json()["models"]:
        assert 0 <= m["performance"]["roc_auc"] <= 1


def test_prediction_runs_and_reports_imputed_features(client, patient_token):
    cases = json.loads((ML_ARTIFACTS / "sample_cases.json").read_text(encoding="utf-8"))
    row = cases["heart"]["positive"]
    r = client.post(
        "/api/predictions/tabular",
        json={"model_key": "heart", "values": row},
        headers={"Authorization": f"Bearer {patient_token}"},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert 0.0 <= body["probability"] <= 1.0
    assert "not a clinically validated probability" in body["probability_interpretation"].lower()
    assert body["explanation"] is not None and body["explanation"]["top_features"]
    assert body["safe_harbour"]


def test_out_of_range_feature_rejected(client, patient_token):
    r = client.post(
        "/api/predictions/tabular",
        json={"model_key": "heart", "values": {"age": 500, "sex": "1"}},
        headers={"Authorization": f"Bearer {patient_token}"},
    )
    assert r.status_code == 422
    assert "above plausible maximum" in r.json()["detail"]


def test_invalid_option_rejected(client, patient_token):
    r = client.post(
        "/api/predictions/tabular",
        json={"model_key": "heart", "values": {"sex": "maybe"}},
        headers={"Authorization": f"Bearer {patient_token}"},
    )
    assert r.status_code == 422
    assert "not a valid option" in r.json()["detail"]


def test_unknown_model_404(client, patient_token):
    r = client.post(
        "/api/predictions/tabular",
        json={"model_key": "nope", "values": {}},
        headers={"Authorization": f"Bearer {patient_token}"},
    )
    assert r.status_code == 404


def test_prediction_requires_auth(client):
    r = client.post("/api/predictions/tabular", json={"model_key": "heart", "values": {}})
    assert r.status_code == 401