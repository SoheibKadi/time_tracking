"""Suite 9 — Application blocklist (5 tests)."""
import pytest


def test_add_pattern(client, worker_headers):
    resp = client.post("/v1/blocklist", headers=worker_headers, json={"pattern": "1Password"})
    assert resp.status_code == 201
    assert resp.json()["pattern"] == "1Password"


def test_list_own_patterns(client, worker_headers):
    client.post("/v1/blocklist", headers=worker_headers, json={"pattern": "KeePass"})
    client.post("/v1/blocklist", headers=worker_headers, json={"pattern": "Bitwarden"})
    resp = client.get("/v1/blocklist", headers=worker_headers)
    assert resp.status_code == 200
    patterns = [i["pattern"] for i in resp.json()]
    assert "KeePass" in patterns
    assert "Bitwarden" in patterns


def test_isolation_between_users(client, worker_headers, worker2_headers):
    client.post("/v1/blocklist", headers=worker_headers, json={"pattern": "SecretApp"})
    resp = client.get("/v1/blocklist", headers=worker2_headers)
    patterns = [i["pattern"] for i in resp.json()]
    assert "SecretApp" not in patterns


def test_delete_pattern(client, worker_headers):
    item_id = client.post(
        "/v1/blocklist", headers=worker_headers, json={"pattern": "Vault"}
    ).json()["id"]
    del_resp = client.delete(f"/v1/blocklist/{item_id}", headers=worker_headers)
    assert del_resp.status_code == 204
    patterns = [i["pattern"] for i in client.get("/v1/blocklist", headers=worker_headers).json()]
    assert "Vault" not in patterns


def test_delete_other_users_pattern(client, worker_headers, worker2_headers):
    item_id = client.post(
        "/v1/blocklist", headers=worker_headers, json={"pattern": "Mine"}
    ).json()["id"]
    resp = client.delete(f"/v1/blocklist/{item_id}", headers=worker2_headers)
    assert resp.status_code == 404
