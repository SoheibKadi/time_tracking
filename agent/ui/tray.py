"""System tray widget — the main UI surface for the agent."""
from PyQt6.QtWidgets import QSystemTrayIcon, QMenu, QApplication
from PyQt6.QtGui import QIcon, QColor, QPixmap
from PyQt6.QtCore import Qt, QMetaObject, Q_ARG, pyqtSlot

from tracker.controller import SessionController
from tracker.sync import SyncAgent
from tracker.config import config


def _make_icon(color: str, size: int = 22) -> QIcon:
    pix = QPixmap(size, size)
    pix.fill(QColor(color))
    return QIcon(pix)


ICONS = {
    "idle":     _make_icon("#9ca3af"),
    "tracking": _make_icon("#22c55e"),
    "paused":   _make_icon("#eab308"),
    "error":    _make_icon("#ef4444"),
}


class TrayIcon(QSystemTrayIcon):
    def __init__(self, app: QApplication):
        super().__init__(ICONS["idle"])
        self._app = app
        self._state = "idle"

        self._controller = SessionController(
            on_state_change=self._on_state_change,
            on_idle_prompt=self._on_idle_prompt,
            on_screenshot_captured=self._on_screenshot_captured,
        )
        self._sync_agent = SyncAgent()

        self._build_menu()
        self.setToolTip("Time Tracker — Idle")
        self.show()

        # Start sync agent immediately
        self._sync_agent.start()

        # macOS permission checks
        self._check_platform_permissions()

        # Login if not configured
        if not config.access_token:
            self._do_login()

        self._controller.start()

    def _check_platform_permissions(self) -> None:
        import sys
        if sys.platform != "darwin":
            return
        from tracker.platform_utils import check_screen_recording_macos, check_accessibility_macos
        if not check_screen_recording_macos():
            self.showMessage(
                "Screen Recording permission needed",
                "Open System Settings → Privacy & Security → Screen Recording and enable Time Tracker, then restart.",
                QSystemTrayIcon.MessageIcon.Warning,
                8000,
            )
        if not check_accessibility_macos():
            self.showMessage(
                "Accessibility permission needed",
                "Open System Settings → Privacy & Security → Accessibility and enable Time Tracker for keyboard/mouse tracking.",
                QSystemTrayIcon.MessageIcon.Warning,
                8000,
            )

    # ── menu ──────────────────────────────────────────────────────────────────

    def _build_menu(self):
        menu = QMenu()
        self._act_start = menu.addAction("▶  Start tracking")
        self._act_pause = menu.addAction("⏸  Pause")
        self._act_stop = menu.addAction("⏹  Stop")
        menu.addSeparator()
        self._act_manual = menu.addAction("📝  Mark as manual...")
        menu.addSeparator()
        menu.addAction("⚙  Preferences", self._do_preferences)
        menu.addAction("🔑  Login", self._do_login)
        menu.addSeparator()
        menu.addAction("Quit", self._app.quit)

        self._act_start.triggered.connect(self._do_start)
        self._act_pause.triggered.connect(self._do_pause)
        self._act_stop.triggered.connect(self._do_stop)
        self._act_manual.triggered.connect(self._do_manual)

        self.setContextMenu(menu)
        self._update_menu_state()

    def _update_menu_state(self):
        tracking = self._state == "tracking"
        self._act_start.setEnabled(self._state in ("idle", "paused"))
        self._act_pause.setEnabled(tracking)
        self._act_stop.setEnabled(tracking or self._state == "paused")
        self._act_manual.setEnabled(tracking)

    # ── actions ───────────────────────────────────────────────────────────────

    def _do_start(self):
        try:
            self._controller.start_tracking()
        except RuntimeError:
            self.showMessage("No contract configured", "Open Preferences to set your Contract ID.", QSystemTrayIcon.MessageIcon.Warning)

    def _do_pause(self):
        self._controller.pause()

    def _do_stop(self):
        self._controller.stop_tracking()

    def _do_manual(self):
        from ui.dialogs import ManualOverrideDialog
        dlg = ManualOverrideDialog()
        if dlg.exec() and dlg.reason():
            self._controller.set_manual_override(dlg.reason())

    def _do_preferences(self):
        from ui.dialogs import PreferencesDialog
        PreferencesDialog().exec()

    def _do_login(self):
        from ui.dialogs import LoginDialog
        LoginDialog().exec()

    # ── controller callbacks (may arrive from non-Qt thread) ─────────────────

    @pyqtSlot(str)
    def _set_state(self, state: str):
        self._state = state
        self.setIcon(ICONS.get(state, ICONS["idle"]))
        label = {"idle": "Idle", "tracking": "Tracking", "paused": "Paused"}.get(state, state.capitalize())
        self.setToolTip(f"Time Tracker — {label}")
        self._update_menu_state()

    def _on_state_change(self, state: str):
        QMetaObject.invokeMethod(self, "_set_state", Qt.ConnectionType.QueuedConnection, Q_ARG(str, state))

    @pyqtSlot()
    def _show_idle_prompt(self):
        from ui.dialogs import IdlePromptDialog
        dlg = IdlePromptDialog()
        if dlg.exec():
            self._controller.confirm_still_working()
        else:
            self._controller.pause()

    def _on_idle_prompt(self):
        QMetaObject.invokeMethod(self, "_show_idle_prompt", Qt.ConnectionType.QueuedConnection)

    @pyqtSlot(str, str)
    def _show_screenshot_preview(self, path: str, window_id: str):
        from ui.dialogs import ScreenshotPreviewDialog
        import httpx
        from tracker.database import SessionLocal
        from tracker.models import LocalScreenshot, LocalWindow, SyncStatus

        dlg = ScreenshotPreviewDialog(path, window_id)
        dlg.exec()

        if dlg.was_deleted():
            # Mark locally and attempt server-side delete if already synced
            db = SessionLocal()
            try:
                ss = db.query(LocalScreenshot).filter(LocalScreenshot.window_id == window_id).first()
                w = db.query(LocalWindow).filter(LocalWindow.id == window_id).first()
                if ss:
                    ss.sync_status = SyncStatus.failed
                    import pathlib
                    pathlib.Path(ss.local_path).unlink(missing_ok=True)
                if w:
                    w.sync_status = SyncStatus.failed
                db.commit()
            finally:
                db.close()
            self.showMessage("Window deleted", "This time window will not be billed.", QSystemTrayIcon.MessageIcon.Information)

    def _on_screenshot_captured(self, path: str, window_id: str):
        QMetaObject.invokeMethod(
            self, "_show_screenshot_preview",
            Qt.ConnectionType.QueuedConnection,
            Q_ARG(str, path), Q_ARG(str, window_id),
        )
