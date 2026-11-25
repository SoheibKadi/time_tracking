"""Suite 6 — Shareable client link and disputes (10 tests)."""
import uuid
from datetime import datetime, timezone, timedelta

import pytest

from tests.backend.conftest import make_window_in_db
from app.models import WindowStatus


def test_client_view(client, contract, session_obj, window):
    resp = client.get(f"/share/{contract['share_token']}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["contract_title"] == contract["title"]
    assert body["billable_hours"] > 0
    assert len(body["windows"]) == 1
    assert "refreshed_at" in body


def test_client_view_invalid_token(client):
    resp = client.get(f"/share/{uuid.uuid4()}")
    assert resp.status_code == 404


def test_billable_hours_excludes_deleted(client, contract, db, session_obj):
    make_window_in_db(db, session_obj["id"], status=WindowStatus.deleted)
    resp = client.get(f"/share/{contract['share_token']}")
    assert resp.json()["billable_hours"] == 0.0


def test_billable_hours_excludes_accepted_dispute(client, contract, db, session_obj):
    make_window_in_db(db, session_obj["id"], status=WindowStatus.accepted_dispute)
    resp = client.get(f"/share/{contract['share_token']}")
    assert resp.json()["billable_hours"] == 0.0


def test_billable_hours_includes_rejected_dispute(client, contract, db, session_obj):
    make_window_in_db(db, session_obj["id"], status=WindowStatus.rejected_dispute)
    resp = client.get(f"/share/{contract['share_token']}")
    assert resp.json()["billable_hours"] > 0.0


def test_client_screenshot_url(client, contract, screenshot):
    resp = client.get(f"/share/{contract['share_token']}/screenshots/{screenshot['id']}")
    assert resp.status_code == 200
    assert "url" in resp.json()


def test_client_dispute_window(client, contract, window):
    resp = client.patch(
        f"/share/{contract['share_token']}/windows/{window['id']}/dispute",
        json={"reason": "I was out of office"},
    )
    assert resp.status_code == 200
    # Window should now appear as disputed in the share view
    view = client.get(f"/share/{contract['share_token']}").json()
    assert view["windows"][0]["status"] == "disputed"
    assert view["windows"][0]["dispute_reason"] == "I was out of office"


def test_client_cannot_dispute_twice(client, contract, db, session_obj):
    w = make_window_in_db(db, session_obj["id"], status=WindowStatus.disputed)
    resp = client.patch(
        f"/share/{contract['share_token']}/windows/{w.id}/dispute",
        json={"reason": "again"},
    )
    assert resp.status_code == 400


def test_client_cannot_dispute_deleted(client, contract, db, session_obj):
    w = make_window_in_db(db, session_obj["id"], status=WindowStatus.deleted)
    resp = client.patch(
        f"/share/{contract['share_token']}/windows/{w.id}/dispute",
        json={},
    )
    assert resp.status_code == 400


def test_websocket_accepts_valid_token(client, contract):
    with client.websocket_connect(f"/share/ws/{contract['share_token']}") as ws:
        pass  # connection accepted and closed cleanly
