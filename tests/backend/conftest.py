"""Backend test fixtures.

Design
------
* Each test gets a fresh file-based SQLite DB (via tmp_path) so there is
  no state leakage between tests and no need for transaction rollbacks.
* `get_db` is overridden to yield the fixture session so app route handlers
  and test setup code share the same connection.
* `app.main._seed_admin` is patched to a no-op — test users are created
  explicitly through helper fixtures.
* External services (MinIO, WeasyPrint) are always mocked.
"""
import uuid
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, MagicMock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.deps import get_db
from app.models import (
    Base, User, UserRole, Organization, FreelancerProfile,
    Contract, ClientProfile, WorkSession, TimeWindow, WindowStatus,
    Screenshot, ActivitySample,
)
from app.services.auth import hash_password

# ── Database fixture ──────────────────────────────────────────────────────────

@pytest.fixture()
def db(tmp_path):
    """Fresh SQLite database for each test."""
    url = f"sqlite:///{tmp_path}/test.db"
    engine = create_engine(url, connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    session = Session()
    yield session
    session.close()
    engine.dispose()


# ── TestClient fixture ────────────────────────────────────────────────────────

@pytest.fixture()
def client(db):
    """FastAPI TestClient with overridden DB and all external services mocked."""

    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    fake_sha256 = "a" * 64

    with patch("app.main._seed_admin"), \
         patch("app.services.storage.upload_screenshot",
               return_value=("screenshots/test.png", "thumbnails/test.jpg", fake_sha256)), \
         patch("app.services.storage.get_presigned_url",
               return_value="https://storage.example.com/img.png"), \
         patch("app.services.storage.delete_object"), \
         patch("app.services.pdf.render_invoice_pdf", return_value=b"%PDF-1.4 fake"):
        yield TestClient(app, raise_server_exceptions=True)

    app.dependency_overrides.clear()


# ── User / auth fixtures ──────────────────────────────────────────────────────

def _make_user(db, email, name, role=UserRole.worker):
    user = User(
        email=email,
        name=name,
        password_hash=hash_password("password123"),
        role=role,
        is_active=True,
    )
    db.add(user)
    db.flush()
    db.add(Organization(name=f"{name}'s Org", owner_id=user.id))
    db.add(FreelancerProfile(user_id=user.id, invoice_prefix="INV"))
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture()
def worker(db):
    return _make_user(db, "worker@test.com", "Test Worker")


@pytest.fixture()
def worker2(db):
    return _make_user(db, "worker2@test.com", "Second Worker")


@pytest.fixture()
def admin_user(db):
    return _make_user(db, "admin@test.com", "Test Admin", role=UserRole.admin)


def _login(client, email, password="password123"):
    resp = client.post("/v1/auth/login", json={"email": email, "password": password})
    assert resp.status_code == 200, resp.text
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


@pytest.fixture()
def worker_headers(client, worker):
    return _login(client, worker.email)


@pytest.fixture()
def worker2_headers(client, worker2):
    return _login(client, worker2.email)


@pytest.fixture()
def admin_headers(client, admin_user):
    return _login(client, admin_user.email)


# ── Domain fixtures ───────────────────────────────────────────────────────────

@pytest.fixture()
def contract(client, worker, worker_headers):
    resp = client.post("/v1/contracts", headers=worker_headers, json={
        "title": "Test Contract",
        "hourly_rate": "50.00",
        "client": {
            "name": "Test Client",
            "billing_email": "client@test.com",
            "billing_address": "123 Client St",
        },
    })
    assert resp.status_code == 201, resp.text
    return resp.json()


@pytest.fixture()
def session_obj(client, contract, worker_headers):
    resp = client.post("/v1/sessions", headers=worker_headers, json={
        "contract_id": contract["id"],
    })
    assert resp.status_code == 201, resp.text
    return resp.json()


@pytest.fixture()
def window(client, session_obj, worker_headers):
    now = datetime.now(timezone.utc)
    resp = client.post("/v1/windows", headers=worker_headers, json={
        "session_id": session_obj["id"],
        "started_at": (now - timedelta(minutes=10)).isoformat(),
        "ended_at": now.isoformat(),
        "activity_level": 7,
    })
    assert resp.status_code == 201, resp.text
    return resp.json()


@pytest.fixture()
def screenshot(client, window, worker_headers):
    resp = client.post(
        "/v1/screenshots",
        headers=worker_headers,
        data={
            "window_id": window["id"],
            "captured_at": datetime.now(timezone.utc).isoformat(),
        },
        files={"file": ("shot.png", b"\x89PNG\r\n\x1a\n", "image/png")},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


# ── Helpers ───────────────────────────────────────────────────────────────────

def make_window_in_db(db, session_id, status=WindowStatus.submitted,
                      minutes_ago=20):
    """Insert a TimeWindow directly into the DB with arbitrary status."""
    now = datetime.now(timezone.utc)
    w = TimeWindow(
        session_id=uuid.UUID(session_id),
        started_at=now - timedelta(minutes=minutes_ago + 10),
        ended_at=now - timedelta(minutes=minutes_ago),
        activity_level=5,
        status=status,
    )
    db.add(w)
    db.commit()
    db.refresh(w)
    return w
