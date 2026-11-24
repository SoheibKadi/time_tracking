"""Activity sampler: counts keystrokes and mouse events using pynput global hooks."""
import math
import threading
from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class _Bucket:
    keystrokes: int = 0
    mouse_clicks: int = 0
    mouse_distance_px: float = 0.0
    _last_pos: tuple = field(default_factory=lambda: (0, 0))


class ActivitySampler:
    """Thread-safe global input hook accumulator."""

    def __init__(self):
        self._lock = threading.Lock()
        self._bucket = _Bucket()
        self._listener_kb = None
        self._listener_mouse = None

    def start(self) -> None:
        from pynput import keyboard, mouse

        def on_key_press(key):
            with self._lock:
                self._bucket.keystrokes += 1

        def on_click(x, y, button, pressed):
            if pressed:
                with self._lock:
                    self._bucket.mouse_clicks += 1

        def on_move(x, y):
            with self._lock:
                lx, ly = self._bucket._last_pos
                dist = math.hypot(x - lx, y - ly)
                self._bucket.mouse_distance_px += dist
                self._bucket._last_pos = (x, y)

        try:
            self._listener_kb = keyboard.Listener(on_press=on_key_press, suppress=False)
            self._listener_kb.start()
        except Exception as exc:
            import logging
            logging.getLogger(__name__).warning(
                "Keyboard listener failed to start (check Accessibility permission on macOS): %s", exc
            )
            self._listener_kb = None

        try:
            self._listener_mouse = mouse.Listener(on_click=on_click, on_move=on_move)
            self._listener_mouse.start()
        except Exception as exc:
            import logging
            logging.getLogger(__name__).warning(
                "Mouse listener failed to start: %s", exc
            )
            self._listener_mouse = None

    def stop(self) -> None:
        if self._listener_kb:
            self._listener_kb.stop()
        if self._listener_mouse:
            self._listener_mouse.stop()

    def flush(self) -> dict:
        """Return current counts and reset the bucket."""
        with self._lock:
            data = {
                "keystrokes": self._bucket.keystrokes,
                "mouse_clicks": self._bucket.mouse_clicks,
                "mouse_distance_px": int(self._bucket.mouse_distance_px),
                "sampled_at": datetime.now(timezone.utc).isoformat(),
            }
            self._bucket = _Bucket()
        return data

    def has_any_activity(self) -> bool:
        with self._lock:
            return bool(self._bucket.keystrokes or self._bucket.mouse_clicks or self._bucket.mouse_distance_px)
