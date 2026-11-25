"""Suite 2 — Contracts & freelancer profile (8 tests)."""
import pytest


def test_create_contract(client, worker_headers):
    resp = client.post("/v1/contracts", headers=worker_headers, json={
        "title": "My Contract",
        "hourly_rate": "75.00",
        "client": {"name": "ACME Corp", "billing_email": "billing@acme.com"},
    })
    assert resp.status_code == 201
    body = resp.json()
    assert body["title"] == "My Contract"
    assert float(body["hourly_rate"]) == 75.0
    assert body["share_token"] is not None
    assert body["client_profile"]["name"] == "ACME Corp"


def test_list_contracts_own_only(client, worker, worker2, worker_headers, worker2_headers):
    # Worker 1 creates a contract
    client.post("/v1/contracts", headers=worker_headers, json={
        "title": "W1 Contract", "hourly_rate": "50.00",
        "client": {"name": "Client A"},
    })
    # Worker 2 creates a contract
    client.post("/v1/contracts", headers=worker2_headers, json={
        "title": "W2 Contract", "hourly_rate": "60.00",
        "client": {"name": "Client B"},
    })
    resp1 = client.get("/v1/contracts", headers=worker_headers)
    resp2 = client.get("/v1/contracts", headers=worker2_headers)
    titles1 = [c["title"] for c in resp1.json()]
    titles2 = [c["title"] for c in resp2.json()]
    assert "W1 Contract" in titles1
    assert "W2 Contract" not in titles1
    assert "W2 Contract" in titles2


def test_get_contract(client, contract, worker_headers):
    resp = client.get(f"/v1/contracts/{contract['id']}", headers=worker_headers)
    assert resp.status_code == 200
    assert resp.json()["id"] == contract["id"]


def test_update_contract_status(client, contract, worker_headers):
    resp = client.patch(
        f"/v1/contracts/{contract['id']}",
        headers=worker_headers,
        json={"status": "paused"},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "paused"


def test_regenerate_share_token(client, contract, worker_headers):
    old_token = contract["share_token"]
    resp = client.post(f"/v1/contracts/{contract['id']}/regenerate-token", headers=worker_headers)
    assert resp.status_code == 200
    new_token = resp.json()["share_token"]
    assert new_token != old_token
    # Old token no longer resolves share view
    assert client.get(f"/share/{old_token}").status_code == 404
    # New token works
    assert client.get(f"/share/{new_token}").status_code == 200


def test_freelancer_profile_upsert(client, worker_headers):
    resp = client.put("/v1/profile", headers=worker_headers, json={
        "company_name": "My LLC",
        "address": "123 Main St",
        "invoice_prefix": "MYCO",
    })
    assert resp.status_code == 200
    assert resp.json()["company_name"] == "My LLC"
    assert resp.json()["invoice_prefix"] == "MYCO"
    # Second update merges
    resp2 = client.put("/v1/profile", headers=worker_headers, json={"address": "456 New Ave"})
    assert resp2.json()["company_name"] == "My LLC"  # preserved
    assert resp2.json()["address"] == "456 New Ave"   # updated


def test_create_contract_unauthenticated(client):
    resp = client.post("/v1/contracts", json={
        "title": "X", "hourly_rate": "10", "client": {"name": "Y"},
    })
    assert resp.status_code == 403  # HTTPBearer returns 403 when no token


def test_contract_not_found(client, worker_headers):
    import uuid
    resp = client.get(f"/v1/contracts/{uuid.uuid4()}", headers=worker_headers)
    assert resp.status_code == 404
