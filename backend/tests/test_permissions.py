def auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _make_user(db, email: str, role: str):
    """Create a user in the test database without re-importing conftest.

    Importing ``tests.conftest`` here would re-execute that module and reset
    ``app.dependency_overrides[get_db]`` to the fallback database, so requests
    would no longer see the per-test database.
    """
    from app.models import User
    from app.security import hash_password

    u = User(
        email=email,
        full_name=email.split("@")[0],
        hashed_password=hash_password("test-password-123"),
        role=role,
    )
    db.add(u)
    db.flush()
    return u


def test_patient_cannot_read_other_profiles(client, db, patient_token):
    other = _make_user(db, "other@test.dev", "patient")
    db.commit()
    from app.models import PatientProfile

    p = PatientProfile(owner_id=other.id, label="someone else")
    db.add(p)
    db.commit()

    r = client.get(f"/api/profiles/{p.id}/completeness", headers=auth(patient_token))
    assert r.status_code == 404

    r = client.get("/api/profiles/shared-with-me", headers=auth(patient_token))
    assert r.status_code == 403


def test_researcher_cannot_read_patient_data(client, patient_token, researcher_token):
    h = auth(patient_token)
    p = client.post("/api/profiles", json={"label": "mine", "is_synthetic": False}, headers=h).json()

    r = client.get(f"/api/profiles/{p['id']}/completeness", headers=auth(researcher_token))
    assert r.status_code == 404

    # the research dataset endpoint only exposes aggregate dataset statistics
    r = client.get("/api/research/datasets", headers=auth(researcher_token))
    assert r.status_code == 200
    assert "manifest" in r.json()


def test_admin_only_endpoints(client, patient_token, clinician_token, researcher_token):
    for tok in (patient_token, clinician_token, researcher_token):
        assert client.get("/api/admin/audit-logs", headers=auth(tok)).status_code == 403


def test_audit_log_written_for_prediction(client, db, patient_token):
    from app.models import AuditLog

    before = db.query(AuditLog).filter_by(action="prediction.tabular").count()
    p = client.post("/api/profiles", json={"label": "audit check"}, headers=auth(patient_token)).json()
    client.post(
        "/api/predictions/tabular",
        json={"model_key": "heart", "values": {"age": 55, "sex": "1"}, "save_to_profile": p["id"]},
        headers=auth(patient_token),
    )
    after = db.query(AuditLog).filter_by(action="prediction.tabular").count()
    assert after == before + 1


def test_patient_grant_flow(client, db, patient_token, clinician_token):
    p = client.post("/api/profiles", json={"label": "grantable"}, headers=auth(patient_token)).json()
    r = client.post(f"/api/profiles/{p['id']}/grants?clinician_email=clinician@test.dev", headers=auth(patient_token))
    assert r.status_code == 201, r.text
    shared = client.get("/api/profiles/shared-with-me", headers=auth(clinician_token)).json()
    assert any(s["profile_id"] == p["id"] for s in shared["shared_profiles"])
