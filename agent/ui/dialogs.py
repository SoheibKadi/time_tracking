"""Preference and setup dialogs."""
from PyQt6.QtWidgets import (
    QDialog, QFormLayout, QLineEdit, QSpinBox,
    QDialogButtonBox, QLabel, QVBoxLayout, QHBoxLayout, QPushButton,
    QTextEdit,
)
from PyQt6.QtCore import Qt

from tracker.config import config


class PreferencesDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Preferences")
        self.setMinimumWidth(420)

        form = QFormLayout()
        self._server = QLineEdit(config.server_url)
        self._contract = QLineEdit(config.contract_id)
        self._interval = QSpinBox()
        self._interval.setRange(1, 60)
        self._interval.setValue(config.screenshot_interval_min)
        self._interval.setSuffix(" min")
        self._idle = QSpinBox()
        self._idle.setRange(1, 30)
        self._idle.setValue(config.idle_timeout_min)
        self._idle.setSuffix(" min")

        form.addRow("Server URL:", self._server)
        form.addRow("Contract ID:", self._contract)
        form.addRow("Screenshot interval:", self._interval)
        form.addRow("Idle timeout:", self._idle)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout()
        layout.addLayout(form)
        layout.addWidget(buttons)
        self.setLayout(layout)

    def _save(self):
        config.server_url = self._server.text().strip()
        config.contract_id = self._contract.text().strip()
        config.screenshot_interval_min = self._interval.value()
        config.idle_timeout_min = self._idle.value()
        config.save()
        self.accept()


class LoginDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Login to Time Tracker")
        self.setMinimumWidth(360)

        form = QFormLayout()
        self._server = QLineEdit(config.server_url or "http://localhost:8000")
        self._email = QLineEdit()
        self._password = QLineEdit()
        self._password.setEchoMode(QLineEdit.EchoMode.Password)

        form.addRow("Server URL:", self._server)
        form.addRow("Email:", self._email)
        form.addRow("Password:", self._password)

        self._status = QLabel("")
        self._status.setStyleSheet("color: red;")

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self._login)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout()
        layout.addLayout(form)
        layout.addWidget(self._status)
        layout.addWidget(buttons)
        self.setLayout(layout)

    def _login(self):
        import httpx
        url = self._server.text().strip()
        try:
            r = httpx.post(
                f"{url}/v1/auth/login",
                json={"email": self._email.text().strip(), "password": self._password.text()},
                timeout=10,
            )
            if r.status_code == 200:
                data = r.json()
                config.server_url = url
                config.access_token = data["access_token"]
                config.refresh_token = data["refresh_token"]
                config.save()
                self.accept()
            else:
                self._status.setText("Invalid email or password.")
        except Exception as exc:
            self._status.setText(f"Connection error: {exc}")


class IdlePromptDialog(QDialog):
    """Non-blocking prompt shown when idle is detected."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Still working?")
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
        self.setFixedWidth(340)

        layout = QVBoxLayout()
        layout.addWidget(QLabel("No activity detected for a while.\nAre you still working?"))

        btn_yes = QPushButton("Yes, keep tracking")
        btn_pause = QPushButton("Pause")
        btn_yes.clicked.connect(self.accept)
        btn_pause.clicked.connect(self.reject)

        h = QHBoxLayout()
        h.addWidget(btn_yes)
        h.addWidget(btn_pause)
        layout.addLayout(h)
        self.setLayout(layout)


class ManualOverrideDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Mark as Manual")
        self.setMinimumWidth(380)

        layout = QVBoxLayout()
        layout.addWidget(QLabel("Reason (e.g. 'In a meeting', 'Watching tutorial'):"))
        self._reason = QTextEdit()
        self._reason.setMaximumHeight(80)
        layout.addWidget(self._reason)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        self.setLayout(layout)

    def reason(self) -> str:
        return self._reason.toPlainText().strip()


class ScreenshotPreviewDialog(QDialog):
    """Grace-period screenshot preview; user can delete before upload."""
    def __init__(self, path: str, window_id: str, parent=None):
        super().__init__(parent)
        self._window_id = window_id
        self._deleted = False
        self.setWindowTitle("Screenshot captured")
        self.setMinimumSize(500, 380)

        from PyQt6.QtWidgets import QScrollArea
        from PyQt6.QtGui import QPixmap
        from PyQt6.QtCore import QTimer

        layout = QVBoxLayout()
        layout.addWidget(QLabel("Screenshot will be uploaded in 60 seconds."))

        pixmap = QPixmap(path).scaled(480, 300, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        img_label = QLabel()
        img_label.setPixmap(pixmap)
        layout.addWidget(img_label)

        self._countdown = QLabel("60s remaining")
        layout.addWidget(self._countdown)

        h = QHBoxLayout()
        btn_ok = QPushButton("OK — upload this")
        btn_delete = QPushButton("Delete (forfeit this window)")
        btn_delete.setStyleSheet("color: red;")
        btn_ok.clicked.connect(self.accept)
        btn_delete.clicked.connect(self._delete)
        h.addWidget(btn_ok)
        h.addWidget(btn_delete)
        layout.addLayout(h)
        self.setLayout(layout)

        self._remaining = 60
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(1000)

    def _tick(self):
        self._remaining -= 1
        self._countdown.setText(f"{self._remaining}s remaining")
        if self._remaining <= 0:
            self._timer.stop()
            self.accept()

    def _delete(self):
        self._deleted = True
        self._timer.stop()
        self.accept()

    def was_deleted(self) -> bool:
        return self._deleted
