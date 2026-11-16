import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db import Base, get_db
from app.main import app
from app.models import PatientProfile, User
from app.security import hash_password

engine = create_engine("sqlite:///./_debug.db", connect_args={"check_same_thread": False})
Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)
Session = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def override():
    s = Session()
    try:
        yield s
    finally:
        s.close()


app.dependency_overrides[get_db] = override
client = TestClient(app)

s = Session()
u = User(email="patient@test.dev", full_name="P", hashed_password=hash_password("test-password-123"), role="patient")
s.add(u)
s.flush()
other = User(email="other@test.dev", full_name="O", hashed_password=hash_password("x"), role="patient")
s.add(other)
s.flush()
p = PatientProfile(owner_id=other.id, label="someone else")
s.add(p)
s.commit()
s.close()

r = client.post("/api/auth/login", json={"email": "patient@test.dev", "password": "test-password-123"})
print("login:", r.status_code)
print("login body keys:", list(r.json().keys()) if r.status_code == 200 else r.text[:300])
if r.status_code == 200:
    import jwt as pyjwt

    token = r.json()["access_token"]
    print("token claims:", pyjwt.decode(token, options={"verify_signature": False}))
    h = {"Authorization": f"Bearer {token}"}
    r2 = client.get(f"/api/profiles/{p.id}/completeness", headers=h)
    print("completeness (other's profile):", r2.status_code, r2.text[:200])
    r3 = client.get("/api/profiles/shared-with-me", headers=h)
    print("shared-with-me:", r3.status_code, r3.text[:200])
    r4 = client.get("/api/auth/me", headers=h)
    print("me:", r4.status_code, r4.text[:200])