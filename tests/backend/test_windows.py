"""Suite 4 — Time windows (9 tests)."""
import uuid
from datetime import datetime, timezone, timedelta

import pytest

from tests.backend.conftest import make_window_in_db
from app.models import WindowStatus


def _now():
    return datetime.now(timezone.utc)


def _window_payload(session_id, *, minutes_ago=10, activity_level=5):
    end = _now()
    return {
        "session_id": session_id,
        "started_at": (end - timedelta(minutes=minutes_ago)).isoformat(),
        "ended_at": end.isoformat(),
        "activity_level": activity_level,
    }


def test_submit_window(client, session_obj, worker_headers):
    resp = client.post("/v1/windows", headers=worker_headers,
                       json=_window_payload(session_obj["id"]))
    assert resp.status_code == 201
    body = resp.json()
    assert body["status"] == "submitted"
    assert body["activity_level"] == 5


def test_submit_window_with_samples(client, session_obj, worker_headers):
    payload = _window_payload(session_obj["id"])
    now = _now()
    payload["activity_samples"] = [
        {"sample_index": i, "keystrokes": 50, "mouse_clicks": 2,
         "mouse_distance_px": 100, "sampled_at": (now - timedelta(minutes=9-i)).isoformat()}
        for i in range(5)
    ]
    resp = client.post("/v1/windows", headers=worker_headers, json=payload)
    assert resp.status_code == 201


def test_submit_manual_window(client, session_obj, worker_headers):
    payload = _window_payload(session_obj["id"])
    payload["is_manual"] = True
    payload["manual_reason"] = "In a client meeting"
    payload["activity_level"] = None
    resp = client.post("/v1/windows", headers=worker_headers, json=payload)
    assert resp.status_code == 201
    body = resp.json()
    assert body["is_manual"] is True
    assert body["manual_reason"] == "In a client meeting"


def test_list_windows_for_contract(client, contract, session_obj, worker_headers):
    for _ in range(3):
        client.post("/v1/windows", headers=worker_headers,
                    json=_window_payload(session_obj["id"]))
    resp = client.get(f"/v1/windows/contract/{contract['id']}", headers=worker_headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 3


def test_resolve_dispute_accept(client, db, session_obj, worker_headers):
    w = make_window_in_db(db, session_obj["id"], status=WindowStatus.disputed)
    resp = client.patch(f"/v1/windows/{w.id}/dispute/resolve",
                        headers=worker_headers, json={"accept": True})
    assert resp.status_code == 200
    assert resp.json()["status"] == "accepted_dispute"
    assert resp.json()["resolved_at"] is not None


def test_resolve_dispute_reject(client, db, session_obj, worker_headers):
    w = make_window_in_db(db, session_obj["id"], status=WindowStatus.disputed)
    resp = client.patch(f"/v1/windows/{w.id}/dispute/resolve",
                        headers=worker_headers, json={"accept": False})
    assert resp.status_code == 200
    assert resp.json()["status"] == "rejected_dispute"


def test_resolve_non_disputed_window(client, db, session_obj, worker_headers):
    w = make_window_in_db(db, session_obj["id"], status=WindowStatus.submitted)
    resp = client.patch(f"/v1/windows/{w.id}/dispute/resolve",
                        headers=worker_headers, json={"accept": True})
    assert resp.status_code == 400


def test_window_resolve_wrong_owner(client, db, worker2, session_obj, worker2_headers):
    w = make_window_in_db(db, session_obj["id"], status=WindowStatus.disputed)
    # worker2 does not own this session
    resp = client.patch(f"/v1/windows/{w.id}/dispute/resolve",
                        headers=worker2_headers, json={"accept": True})
    assert resp.status_code == 404


def test_window_submit_marks_pending_update(client, session_obj, contract, worker_headers):
    from app.ws import pending_updates
    pending_updates.clear()
    client.post("/v1/windows", headers=worker_headers,
                json=_window_payload(session_obj["id"]))
    assert contract["share_token"] in pending_updates
