import sys
from pathlib import Path

import pytest

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

from app import ml_bridge  # noqa: E402,F401  (adds ml/src to sys.path)
from app.db import Base, get_db  # noqa: E402
from app.main import app  # noqa: E402
from app.models import User  # noqa: E402
from app.security import hash_password  # noqa: E402

engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def override_get_db():
    db = TestingSession()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="session", autouse=True)
def _db():
    Base.metadata.create_all(bind=engine)
    yield


@pytest.fixture()
def db():
    # Fresh schema per test: the in-memory DB is session-scoped for speed, but
    # each test must not see rows seeded by earlier tests.
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    session = TestingSession()
    yield session
    session.rollback()
    session.close()


@pytest.fixture()
def client():
    return TestClient(app)


def make_user(db, email: str, role: str) -> User:
    u = User(email=email, full_name=email.split("@")[0], hashed_password=hash_password("test-password-123"), role=role)
    db.add(u)
    db.flush()
    return u


@pytest.fixture()
def patient_token(db, client):
    make_user(db, "patient@test.dev", "patient")
    db.commit()
    r = client.post("/api/auth/login", json={"email": "patient@test.dev", "password": "test-password-123"})
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


@pytest.fixture()
def clinician_token(db, client):
    make_user(db, "clinician@test.dev", "clinician")
    db.commit()
    r = client.post("/api/auth/login", json={"email": "clinician@test.dev", "password": "test-password-123"})
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


@pytest.fixture()
def researcher_token(db, client):
    make_user(db, "researcher@test.dev", "researcher")
    db.commit()
    r = client.post("/api/auth/login", json={"email": "researcher@test.dev", "password": "test-password-123"})
    assert r.status_code == 200, r.text
    return r.json()["access_token"]