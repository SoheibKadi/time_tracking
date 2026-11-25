"""Suite 8 — Admin panel (7 tests)."""
import pytest


def test_list_users_admin(client, admin_headers, worker, worker2):
    resp = client.get("/v1/admin/users", headers=admin_headers)
    assert resp.status_code == 200
    emails = [u["email"] for u in resp.json()]
    assert worker.email in emails
    assert worker2.email in emails


def test_list_users_worker_forbidden(client, worker_headers):
    resp = client.get("/v1/admin/users", headers=worker_headers)
    assert resp.status_code == 403


def test_deactivate_user(client, admin_headers, worker):
    resp = client.patch(f"/v1/admin/users/{worker.id}",
                        headers=admin_headers, json={"is_active": False})
    assert resp.status_code == 200
    assert resp.json()["is_active"] is False
    # User can no longer log in
    login = client.post("/v1/auth/login",
                        json={"email": worker.email, "password": "password123"})
    assert login.status_code == 401


def test_reactivate_user(client, admin_headers, db, worker):
    worker.is_active = False
    db.commit()
    resp = client.patch(f"/v1/admin/users/{worker.id}",
                        headers=admin_headers, json={"is_active": True})
    assert resp.status_code == 200
    login = client.post("/v1/auth/login",
                        json={"email": worker.email, "password": "password123"})
    assert login.status_code == 200


def test_invite_user(client, admin_headers):
    resp = client.post("/v1/admin/users/invite", headers=admin_headers, json={
        "email": "invited@test.com", "name": "Invited User", "role": "worker",
    })
    assert resp.status_code == 201
    body = resp.json()
    assert "temp_password" in body
    # Invited user can log in with the temp password
    login = client.post("/v1/auth/login",
                        json={"email": "invited@test.com", "password": body["temp_password"]})
    assert login.status_code == 200


def test_audit_log_has_entries(client, admin_headers, worker):
    client.patch(f"/v1/admin/users/{worker.id}",
                 headers=admin_headers, json={"is_active": False})
    resp = client.get("/v1/admin/audit", headers=admin_headers)
    assert resp.status_code == 200
    actions = [e["action"] for e in resp.json()]
    assert "user.deactivate" in actions


def test_audit_log_worker_forbidden(client, worker_headers):
    resp = client.get("/v1/admin/audit", headers=worker_headers)
    assert resp.status_code == 403
