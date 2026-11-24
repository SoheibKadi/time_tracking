"""HTTP sync agent: uploads pending windows and screenshots to the backend."""
import logging
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

import httpx

from tracker.config import config
from tracker.database import SessionLocal
from tracker.models import LocalWindow, LocalScreenshot, SyncStatus, LocalSession

logger = logging.getLogger(__name__)

_RETRY_INTERVAL = 300   # seconds between sync attempts
_MAX_BACKOFF = 3600


class SyncAgent(threading.Thread):
    def __init__(self):
        super().__init__(daemon=True, name="SyncAgent")
        self._stop_event = threading.Event()
        self._backoff = _RETRY_INTERVAL

    def stop(self) -> None:
        self._stop_event.set()

    def run(self) -> None:
        while not self._stop_event.is_set():
            try:
                self._sync()
                self._backoff = _RETRY_INTERVAL
            except Exception as exc:
                logger.warning("Sync error: %s", exc)
                self._backoff = min(self._backoff * 2, _MAX_BACKOFF)
            self._stop_event.wait(self._backoff)

    # ── internal ──────────────────────────────────────────────────────────────

    def _client(self) -> httpx.Client:
        return httpx.Client(
            base_url=config.server_url,
            headers={"Authorization": f"Bearer {config.access_token}"},
            timeout=30,
        )

    def _refresh_token_if_needed(self, client: httpx.Client) -> bool:
        resp = client.get("/v1/contracts")
        if resp.status_code != 401:
            return True
        # Try refreshing
        r = httpx.post(
            f"{config.server_url}/v1/auth/refresh",
            json={"refresh_token": config.refresh_token},
            timeout=15,
        )
        if r.status_code == 200:
            data = r.json()
            config.access_token = data["access_token"]
            config.refresh_token = data["refresh_token"]
            config.save()
            client.headers["Authorization"] = f"Bearer {config.access_token}"
            return True
        return False

    def _sync(self) -> None:
        with self._client() as client:
            if not self._refresh_token_if_needed(client):
                logger.warning("Authentication failed; skipping sync")
                return
            self._sync_sessions(client)
            self._sync_windows(client)
            self._sync_screenshots(client)

    def _sync_sessions(self, client: httpx.Client) -> None:
        db = SessionLocal()
        try:
            pending = db.query(LocalSession).filter(
                LocalSession.remote_session_id.is_(None),
                LocalSession.is_active == True,
            ).all()
            for s in pending:
                r = client.post("/v1/sessions", json={"contract_id": s.contract_id})
                if r.status_code == 201:
                    s.remote_session_id = r.json()["id"]
            db.commit()
        finally:
            db.close()

    def _sync_windows(self, client: httpx.Client) -> None:
        db = SessionLocal()
        try:
            pending = db.query(LocalWindow).filter(LocalWindow.sync_status == SyncStatus.pending).all()
            for w in pending:
                session = db.query(LocalSession).filter(LocalSession.id == w.session_id).first()
                if not session or not session.remote_session_id:
                    continue
                samples = []
                from tracker.models import LocalActivitySample
                for s in db.query(LocalActivitySample).filter(LocalActivitySample.window_id == w.id).all():
                    samples.append({
                        "sample_index": s.sample_index,
                        "keystrokes": s.keystrokes,
                        "mouse_clicks": s.mouse_clicks,
                        "mouse_distance_px": s.mouse_distance_px,
                        "sampled_at": s.sampled_at.isoformat(),
                    })
                payload = {
                    "session_id": session.remote_session_id,
                    "started_at": w.started_at.isoformat(),
                    "ended_at": w.ended_at.isoformat(),
                    "activity_level": w.activity_level,
                    "is_manual": w.is_manual,
                    "manual_reason": w.manual_reason,
                    "activity_samples": samples,
                }
                r = client.post("/v1/windows", json=payload)
                if r.status_code == 201:
                    w.remote_id = r.json()["id"]
                    w.sync_status = SyncStatus.uploaded
                else:
                    w.sync_status = SyncStatus.failed
            db.commit()
        finally:
            db.close()

    def _sync_screenshots(self, client: httpx.Client) -> None:
        db = SessionLocal()
        try:
            pending = db.query(LocalScreenshot).filter(LocalScreenshot.sync_status == SyncStatus.pending).all()
            for s in pending:
                window = db.query(LocalWindow).filter(LocalWindow.id == s.window_id).first()
                if not window or not window.remote_id:
                    continue
                path = Path(s.local_path)
                if not path.exists():
                    s.sync_status = SyncStatus.failed
                    continue
                with open(path, "rb") as f:
                    r = client.post(
                        "/v1/screenshots",
                        data={"window_id": window.remote_id, "captured_at": s.captured_at.isoformat()},
                        files={"file": ("screenshot.png", f, "image/png")},
                    )
                if r.status_code == 201:
                    s.sync_status = SyncStatus.uploaded
                    path.unlink(missing_ok=True)
                else:
                    s.sync_status = SyncStatus.failed
            db.commit()
        finally:
            db.close()
