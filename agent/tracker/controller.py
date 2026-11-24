"""Session / window state machine for the agent."""
import random
import threading
import time
import logging
from datetime import datetime, timezone
from typing import Callable, Optional

from tracker.config import config
from tracker.database import SessionLocal
from tracker.models import LocalSession, LocalWindow, LocalActivitySample, LocalScreenshot, SyncStatus
from tracker.activity import ActivitySampler
from tracker import screenshot as sc

logger = logging.getLogger(__name__)

SAMPLE_INTERVAL = 60    # seconds per activity sample
WINDOW_DURATION = 600   # 10 minutes per window


class SessionController(threading.Thread):
    """Drives the tracking loop in a background thread.

    Emits callbacks so the UI can react:
      on_state_change(state: str)   -- 'idle' | 'tracking' | 'paused'
      on_idle_prompt()              -- ask user if still working
      on_screenshot_captured(path)  -- show preview / grace-period dialog
    """

    def __init__(
        self,
        on_state_change: Callable[[str], None],
        on_idle_prompt: Callable[[], None],
        on_screenshot_captured: Callable[[str, str], None],
    ):
        super().__init__(daemon=True, name="SessionController")
        self._on_state_change = on_state_change
        self._on_idle_prompt = on_idle_prompt
        self._on_screenshot_captured = on_screenshot_captured

        self._stop = threading.Event()
        self._paused = threading.Event()
        self._paused.set()   # start paused (idle)

        self._sampler = ActivitySampler()
        self._current_session: Optional[LocalSession] = None
        self._current_window: Optional[LocalWindow] = None
        self._window_start: Optional[datetime] = None
        self._sample_index = 0
        self._idle_ticks = 0
        self._manual_pending: Optional[str] = None  # manual reason queued

    # ── public control API (called from UI thread) ────────────────────────────

    def start_tracking(self) -> None:
        if not config.contract_id:
            raise RuntimeError("No contract configured")
        self._ensure_session()
        self._start_window()
        self._paused.clear()
        self._sampler.start()
        self._on_state_change("tracking")

    def pause(self) -> None:
        self._paused.set()
        self._sampler.stop()
        self._close_current_window()
        self._on_state_change("paused")

    def stop_tracking(self) -> None:
        self._paused.set()
        self._sampler.stop()
        self._close_current_window()
        self._close_session()
        self._on_state_change("idle")

    def confirm_still_working(self) -> None:
        """User responded 'yes' to idle prompt."""
        self._idle_ticks = 0

    def set_manual_override(self, reason: str) -> None:
        """Mark the current (or next) window as manual."""
        self._manual_pending = reason
        if self._current_window:
            db = SessionLocal()
            try:
                w = db.query(LocalWindow).filter(LocalWindow.id == self._current_window.id).first()
                if w:
                    w.is_manual = True
                    w.manual_reason = reason
                    db.commit()
            finally:
                db.close()
        self._manual_pending = None

    # ── thread loop ───────────────────────────────────────────────────────────

    def run(self) -> None:
        while not self._stop.wait(SAMPLE_INTERVAL):
            if self._paused.is_set():
                self._idle_ticks = 0
                continue

            sample = self._sampler.flush()
            has_activity = bool(sample["keystrokes"] or sample["mouse_clicks"])

            self._save_sample(sample)
            self._sample_index += 1

            if not has_activity:
                self._idle_ticks += 1
                idle_minutes = self._idle_ticks * SAMPLE_INTERVAL / 60
                if idle_minutes >= config.idle_timeout_min:
                    self._on_idle_prompt()
                    # Give the user `idle_autopause_sec` to respond before auto-pausing
                    time.sleep(config.idle_autopause_sec)
                    if self._idle_ticks > 0:  # still idle — auto-pause
                        self.pause()
                    continue
            else:
                self._idle_ticks = 0

            # Close window every 10 samples (10 min)
            if self._sample_index >= WINDOW_DURATION // SAMPLE_INTERVAL:
                self._close_current_window()
                self._start_window()

    def _ensure_session(self) -> None:
        db = SessionLocal()
        try:
            active = db.query(LocalSession).filter(
                LocalSession.contract_id == config.contract_id,
                LocalSession.is_active == True,
            ).first()
            if not active:
                active = LocalSession(contract_id=config.contract_id)
                db.add(active)
                db.commit()
                db.refresh(active)
            self._current_session = active
        finally:
            db.close()

    def _start_window(self) -> None:
        self._window_start = datetime.now(timezone.utc)
        self._sample_index = 0
        db = SessionLocal()
        try:
            w = LocalWindow(
                session_id=self._current_session.id,
                contract_id=config.contract_id,
                started_at=self._window_start,
                ended_at=self._window_start,  # will be updated on close
                is_manual=bool(self._manual_pending),
                manual_reason=self._manual_pending,
            )
            db.add(w)
            db.commit()
            db.refresh(w)
            self._current_window = w
            self._manual_pending = None

            # Schedule screenshot at a random offset within the window
            offset = random.randint(30, WINDOW_DURATION - 30)
            threading.Timer(offset, self._take_screenshot).start()
        finally:
            db.close()

    def _close_current_window(self) -> None:
        if not self._current_window:
            return
        db = SessionLocal()
        try:
            w = db.query(LocalWindow).filter(LocalWindow.id == self._current_window.id).first()
            if w:
                w.ended_at = datetime.now(timezone.utc)
                w.activity_level = self._compute_activity_level(w.id, db)
                db.commit()
        finally:
            db.close()
        self._current_window = None

    def _close_session(self) -> None:
        if not self._current_session:
            return
        db = SessionLocal()
        try:
            s = db.query(LocalSession).filter(LocalSession.id == self._current_session.id).first()
            if s:
                s.is_active = False
                db.commit()
        finally:
            db.close()
        self._current_session = None

    def _save_sample(self, sample: dict) -> None:
        if not self._current_window:
            return
        db = SessionLocal()
        try:
            db.add(LocalActivitySample(
                window_id=self._current_window.id,
                sample_index=self._sample_index,
                keystrokes=sample["keystrokes"],
                mouse_clicks=sample["mouse_clicks"],
                mouse_distance_px=sample["mouse_distance_px"],
                sampled_at=datetime.fromisoformat(sample["sampled_at"].replace("Z", "+00:00")),
            ))
            db.commit()
        finally:
            db.close()

    def _take_screenshot(self) -> None:
        if self._paused.is_set() or not self._current_window:
            return
        try:
            data, sha256, captured_at = sc.capture()
            path = sc.save_to_spool(self._current_window.id, data)
            db = SessionLocal()
            try:
                db.add(LocalScreenshot(
                    window_id=self._current_window.id,
                    captured_at=captured_at,
                    local_path=str(path),
                    sha256=sha256,
                ))
                db.commit()
            finally:
                db.close()
            self._on_screenshot_captured(str(path), self._current_window.id)
        except Exception as exc:
            logger.error("Screenshot failed: %s", exc)

    def _compute_activity_level(self, window_id: str, db) -> int:
        samples = db.query(LocalActivitySample).filter(LocalActivitySample.window_id == window_id).all()
        total_keys = sum(s.keystrokes for s in samples)
        total_clicks = sum(s.mouse_clicks for s in samples)
        score = (total_keys + total_clicks * 5) / config.activity_scale_factor
        return max(0, min(10, round(score)))
