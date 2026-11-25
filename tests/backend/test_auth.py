"""Suite 1 — Authentication (8 tests)."""
import pytest


def test_login_valid(client, worker):
    resp = client.post("/v1/auth/login", json={"email": worker.email, "password": "password123"})
    assert resp.status_code == 200
    body = resp.json()
    assert "access_token" in body
    assert "refresh_token" in body
    assert body["token_type"] == "bearer"


def test_login_wrong_password(client, worker):
    resp = client.post("/v1/auth/login", json={"email": worker.email, "password": "wrong"})
    assert resp.status_code == 401


def test_login_unknown_email(client):
    resp = client.post("/v1/auth/login", json={"email": "nobody@test.com", "password": "x"})
    assert resp.status_code == 401


def test_login_inactive_user(client, db, worker):
    worker.is_active = False
    db.commit()
    resp = client.post("/v1/auth/login", json={"email": worker.email, "password": "password123"})
    assert resp.status_code == 401


def test_refresh_token(client, worker, worker_headers):
    login = client.post("/v1/auth/login", json={"email": worker.email, "password": "password123"})
    refresh_token = login.json()["refresh_token"]
    resp = client.post("/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert resp.status_code == 200
    assert "access_token" in resp.json()


def test_refresh_invalid_token(client):
    resp = client.post("/v1/auth/refresh", json={"refresh_token": "garbage.token.here"})
    assert resp.status_code == 401


def test_me_returns_role_and_email(client, worker, worker_headers):
    resp = client.get("/v1/auth/me", headers=worker_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["email"] == worker.email
    assert body["role"] == "worker"
    assert body["is_active"] is True


def test_register_when_disabled(client, monkeypatch):
    monkeypatch.setattr("app.config.settings.ALLOW_REGISTRATION", False)
    resp = client.post("/v1/auth/register", json={
        "email": "new@test.com", "name": "New", "password": "pass1234"
    })
    assert resp.status_code == 404


def test_register_when_enabled(client):
    resp = client.post("/v1/auth/register", json={
        "email": "new@test.com", "name": "New User", "password": "pass1234"
    })
    assert resp.status_code == 201
    # Can now log in
    login = client.post("/v1/auth/login", json={"email": "new@test.com", "password": "pass1234"})
    assert login.status_code == 200
