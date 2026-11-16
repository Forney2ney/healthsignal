def auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def test_report_generation_and_markdown(client, patient_token):
    p = client.post("/api/profiles", json={"label": "report profile"}, headers=auth(patient_token)).json()
    for kind, value in (("age", 54), ("systolic_bp", 126)):
        client.post(
            f"/api/profiles/{p['id']}/measurements",
            json={"kind": kind, "value": value},
            headers=auth(patient_token),
        )
    client.post(
        "/api/predictions/tabular",
        json={"model_key": "heart", "values": {"age": 54, "sex": "1"}, "save_to_profile": p["id"]},
        headers=auth(patient_token),
    )

    r = client.get(f"/api/reports/profile/{p['id']}", headers=auth(patient_token))
    assert r.status_code == 200
    body = r.json()
    assert body["model_outputs"] and body["model_outputs"][0]["probability"] >= 0
    assert "not a medical diagnosis" in body["safe_harbour"].lower()
    assert body["patient_provided"]["measurements"]["age"] == 54
    assert body["limitations"]

    md = client.get(f"/api/reports/profile/{p['id']}/markdown", headers=auth(patient_token))
    assert md.status_code == 200 and "ai-generated, not a diagnosis" in md.text.lower()


def test_report_requires_auth(client):
    assert client.get("/api/reports/profile/1").status_code == 401


def test_report_404_for_unknown_profile(client, patient_token):
    assert client.get("/api/reports/profile/9999", headers=auth(patient_token)).status_code == 404


def test_assistant_grounds_answers(client, patient_token):
    r = client.post("/api/assistant/ask", json={"question": "what does the chest X-ray model do?"},
                    headers=auth(patient_token))
    assert r.status_code == 200
    body = r.json()
    assert "NIH ChestX-ray14" in body["answer"]
    assert body["uncertainty"]

    r = client.post("/api/assistant/ask", json={"question": "tell me about my unicorn test results"},
                    headers=auth(patient_token))
    assert r.status_code == 200