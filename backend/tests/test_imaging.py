import json
from pathlib import Path

import pytest

SAMPLES_DIR = Path(__file__).resolve().parents[1] / "assets" / "samples"


def auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def test_image_samples_available(client):
    r = client.get("/api/imaging/samples")
    assert r.status_code == 200
    assert r.json()["samples"], "run ml/scripts/fetch_samples.py"


def test_sample_analysis_produces_gradcam(client, patient_token):
    samples = client.get("/api/imaging/samples").json()["samples"]
    r = client.post(
        "/api/imaging/analyze-sample",
        json={"model_key": "cxr_nih", "sample_file": samples[0]},
        headers=auth(patient_token),
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["labels"]
    assert all(0.0 <= v <= 1.0 for v in body["probabilities"].values())
    assert body["highest_label"]
    assert body["gradcam"] and body["gradcam"]["overlay_png_b64"]
    assert "not an individual disease probability" in body["probability_interpretation"].lower()
    assert "not" in body["gradcam"]["cam_explanation"].lower()


def test_upload_rejects_bad_extension(client, patient_token, tmp_path):
    bad = tmp_path / "notes.txt"
    bad.write_text("hello")
    r = client.post(
        "/api/imaging/upload",
        files={"file": ("notes.txt", b"hello", "text/plain")},
        headers=auth(patient_token),
    )
    assert r.status_code == 422


def test_upload_rejects_fake_png(client, patient_token, tmp_path):
    fake = tmp_path / "scan.png"
    fake.write_bytes(b"MZ not really a png")
    r = client.post(
        "/api/imaging/upload",
        files={"file": ("scan.png", b"MZ not really a png", "image/png")},
        headers=auth(patient_token),
    )
    assert r.status_code == 422


def test_upload_accepts_real_png_and_analyzes(client, patient_token):
    samples = client.get("/api/imaging/samples").json()["samples"]
    path = SAMPLES_DIR / samples[0]
    r = client.post(
        "/api/imaging/upload",
        files={"file": (path.name, path.read_bytes(), "image/png")},
        headers=auth(patient_token),
    )
    assert r.status_code == 201, r.text
    study_id = r.json()["study_id"]
    out = client.post(f"/api/imaging/analyze/{study_id}", json={"model_key": "cxr_nih"},
                      headers=auth(patient_token))
    assert out.status_code == 200, out.text
    assert out.json()["highest_label"]


@pytest.mark.skipif(not SAMPLES_DIR.exists(), reason="no sample images")
def test_sample_files_exist():
    assert list(SAMPLES_DIR.glob("*.png"))