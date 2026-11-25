"""Suite 5 — Screenshots (6 tests)."""
import uuid
from datetime import datetime, timezone, timedelta

import pytest

from app.models import Screenshot, TimeWindow, WindowStatus


def _upload(client, window_id, headers):
    return client.post(
        "/v1/screenshots",
        headers=headers,
        data={"window_id": window_id, "captured_at": datetime.now(timezone.utc).isoformat()},
        files={"file": ("shot.png", b"\x89PNG\r\n\x1a\n", "image/png")},
    )


def test_upload_screenshot(client, window, worker_headers):
    resp = _upload(client, window["id"], worker_headers)
    assert resp.status_code == 201
    body = resp.json()
    assert body["window_id"] == window["id"]
    assert len(body["sha256"]) == 64


def test_upload_duplicate_screenshot(client, window, worker_headers):
    _upload(client, window["id"], worker_headers)
    resp = _upload(client, window["id"], worker_headers)
    assert resp.status_code == 409


def test_get_screenshot_image_url(client, screenshot, worker_headers):
    resp = client.get(f"/v1/screenshots/{screenshot['id']}/image", headers=worker_headers)
    assert resp.status_code == 200
    assert "url" in resp.json()


def test_delete_within_grace_period(client, screenshot, worker_headers, db):
    resp = client.delete(f"/v1/screenshots/{screenshot['id']}", headers=worker_headers)
    assert resp.status_code == 204
    # Window should now be marked deleted
    window = db.query(TimeWindow).filter(
        TimeWindow.id == uuid.UUID(screenshot["window_id"])
    ).first()
    assert window.status == WindowStatus.deleted


def test_delete_after_grace_period(client, db, window, worker_headers):
    # Insert screenshot directly with captured_at > 60s ago
    ss = Screenshot(
        window_id=uuid.UUID(window["id"]),
        captured_at=datetime.now(timezone.utc) - timedelta(seconds=120),
        storage_key="screenshots/old.png",
        sha256="b" * 64,
    )
    db.add(ss)
    db.commit()
    db.refresh(ss)

    resp = client.delete(f"/v1/screenshots/{ss.id}", headers=worker_headers)
    assert resp.status_code == 400


def test_delete_screenshot_wrong_owner(client, screenshot, worker2_headers):
    resp = client.delete(f"/v1/screenshots/{screenshot['id']}", headers=worker2_headers)
    assert resp.status_code == 404
