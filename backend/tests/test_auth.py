def test_register_login_me(client, db):
    r = client.post("/api/auth/register", json={
        "email": "new@test.dev", "full_name": "New User",
        "password": "long-enough-password", "role": "patient",
    })
    assert r.status_code == 201, r.text
    token = r.json()["access_token"]

    me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["role"] == "patient"


def test_duplicate_email_rejected(client, db):
    client.post("/api/auth/register", json={
        "email": "dup@test.dev", "full_name": "Dup",
        "password": "long-enough-password", "role": "patient",
    })
    r = client.post("/api/auth/register", json={
        "email": "dup@test.dev", "full_name": "Dup2",
        "password": "long-enough-password", "role": "patient",
    })
    assert r.status_code == 409


def test_short_password_rejected(client):
    r = client.post("/api/auth/register", json={
        "email": "weak@test.dev", "full_name": "Weak",
        "password": "short", "role": "patient",
    })
    assert r.status_code == 422


def test_bad_login_rejected(client):
    r = client.post("/api/auth/login", json={"email": "nobody@test.dev", "password": "whatever-or"})
    assert r.status_code == 401


def test_me_requires_auth(client):
    r = client.get("/api/auth/me")
    assert r.status_code == 401