"""Entry point for the Time Tracker desktop agent."""
import sys
import logging

from PyQt6.QtWidgets import QApplication

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s %(message)s")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    app.setApplicationName("Time Tracker")

    if not QApplication.isSystemTrayAvailable():
        print("System tray not available on this system.", file=sys.stderr)
        sys.exit(1)

    from ui.tray import TrayIcon
    tray = TrayIcon(app)

    sys.exit(app.exec())
