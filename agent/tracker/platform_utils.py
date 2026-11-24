"""Platform-specific foreground window detection.

Returns (window_title, process_name) for the currently active window.
Used by the blocklist checker before capturing a screenshot.
"""
import sys
import subprocess
import logging

logger = logging.getLogger(__name__)


def get_foreground_window() -> tuple[str, str]:
    """Return (window_title, process_name). Both empty strings on failure."""
    try:
        if sys.platform == "win32":
            return _win32()
        elif sys.platform == "darwin":
            return _macos()
        else:
            return _linux()
    except Exception as exc:
        logger.debug("foreground window detection failed: %s", exc)
        return "", ""


def _win32() -> tuple[str, str]:
    try:
        import win32gui
        import win32process
        import psutil
        hwnd = win32gui.GetForegroundWindow()
        title = win32gui.GetWindowText(hwnd)
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        name = psutil.Process(pid).name()
        return title, name
    except ImportError:
        # pywin32 / psutil not installed — fall back to subprocess
        return _win32_powershell()


def _win32_powershell() -> tuple[str, str]:
    r = subprocess.run(
        ["powershell", "-NoProfile", "-Command",
         "(Get-Process | Where-Object {$_.MainWindowTitle -ne ''} | Sort-Object -Descending CPU | Select-Object -First 1).MainWindowTitle"],
        capture_output=True, text=True, timeout=3,
    )
    return r.stdout.strip(), ""


def _macos() -> tuple[str, str]:
    r = subprocess.run(
        ["osascript", "-e",
         'tell application "System Events" to get {name of first process whose frontmost is true}'],
        capture_output=True, text=True, timeout=3,
    )
    name = r.stdout.strip()
    return name, name


def _linux() -> tuple[str, str]:
    # Requires xdotool (X11 only; Wayland not supported)
    r = subprocess.run(
        ["xdotool", "getactivewindow", "getwindowname"],
        capture_output=True, text=True, timeout=3,
    )
    return r.stdout.strip(), ""


# ── macOS permission helpers ───────────────────────────────────────────────────

def check_screen_recording_macos() -> bool:
    """Return True if screen recording is accessible (macOS only)."""
    if sys.platform != "darwin":
        return True
    try:
        import mss
        with mss.mss() as sct:
            sct.grab(sct.monitors[1])
        return True
    except Exception:
        return False


def check_accessibility_macos() -> bool:
    """Return True if Accessibility permission is granted (macOS only)."""
    if sys.platform != "darwin":
        return True
    try:
        result = subprocess.run(
            ["osascript", "-e",
             'tell application "System Events" to get name of first process whose frontmost is true'],
            capture_output=True, text=True, timeout=3,
        )
        return result.returncode == 0
    except Exception:
        return False
