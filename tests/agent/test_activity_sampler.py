"""Suite A — ActivitySampler (6 tests).

pynput is mocked by tests/agent/conftest.py so no hardware hooks are needed.
The sampler's accumulation logic is tested by directly calling the internal
listener callbacks.
"""
import math
import pytest

from tracker.activity import ActivitySampler


def _sampler():
    s = ActivitySampler()
    # Don't call start() — that would attach real OS hooks.
    # We feed events by calling the private callbacks directly.
    return s


def test_flush_returns_zero_initially():
    s = _sampler()
    data = s.flush()
    assert data["keystrokes"] == 0
    assert data["mouse_clicks"] == 0
    assert data["mouse_distance_px"] == 0


def test_keystrokes_accumulated():
    s = _sampler()
    for _ in range(5):
        s._bucket.keystrokes += 1   # simulate on_key_press
    data = s.flush()
    assert data["keystrokes"] == 5


def test_mouse_clicks_accumulated():
    s = _sampler()
    s._bucket.mouse_clicks += 3
    data = s.flush()
    assert data["mouse_clicks"] == 3


def test_mouse_distance_accumulated():
    s = _sampler()
    # Simulate move from (0,0) to (3,4): distance = 5
    x0, y0 = 0, 0
    x1, y1 = 3, 4
    s._bucket.mouse_distance_px += math.hypot(x1 - x0, y1 - y0)
    s._bucket._last_pos = (x1, y1)
    data = s.flush()
    assert data["mouse_distance_px"] == 5


def test_flush_resets_counts():
    s = _sampler()
    s._bucket.keystrokes = 10
    s._bucket.mouse_clicks = 5
    s.flush()
    second = s.flush()
    assert second["keystrokes"] == 0
    assert second["mouse_clicks"] == 0


def test_has_any_activity():
    s = _sampler()
    assert s.has_any_activity() is False
    s._bucket.keystrokes = 1
    assert s.has_any_activity() is True
