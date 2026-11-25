"""Suite 3 — Work sessions (5 tests)."""
import pytest


def test_start_session(client, contract, worker_headers):
    resp = client.post("/v1/sessions", headers=worker_headers, json={
        "contract_id": contract["id"],
    })
    assert resp.status_code == 201
    body = resp.json()
    assert body["contract_id"] == contract["id"]
    assert body["ended_at"] is None


def test_start_session_on_paused_contract(client, contract, worker_headers):
    client.patch(f"/v1/contracts/{contract['id']}", headers=worker_headers,
                 json={"status": "paused"})
    resp = client.post("/v1/sessions", headers=worker_headers, json={
        "contract_id": contract["id"],
    })
    assert resp.status_code == 400


def test_stop_session(client, session_obj, worker_headers):
    resp = client.patch(f"/v1/sessions/{session_obj['id']}", headers=worker_headers,
                        json={"action": "stop"})
    assert resp.status_code == 200
    assert resp.json()["ended_at"] is not None


def test_stop_already_stopped_session(client, session_obj, worker_headers):
    client.patch(f"/v1/sessions/{session_obj['id']}", headers=worker_headers,
                 json={"action": "stop"})
    first_ended = client.patch(
        f"/v1/sessions/{session_obj['id']}", headers=worker_headers, json={"action": "stop"}
    ).json()["ended_at"]
    # Stopped again — ended_at must NOT change
    second = client.patch(
        f"/v1/sessions/{session_obj['id']}", headers=worker_headers, json={"action": "stop"}
    )
    assert second.status_code == 200
    assert second.json()["ended_at"] == first_ended


def test_list_sessions_for_contract(client, contract, session_obj, worker_headers):
    # Create a second session
    client.post("/v1/sessions", headers=worker_headers, json={"contract_id": contract["id"]})
    resp = client.get(f"/v1/sessions/contract/{contract['id']}", headers=worker_headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 2
