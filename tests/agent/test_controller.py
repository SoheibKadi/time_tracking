"""Suite C — SessionController pure logic (5 tests)."""
import uuid
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from tracker.controller import SessionController
from tracker.config import config


def _controller():
    """Instantiate a SessionController without starting any threads."""
    c = SessionController.__new__(SessionController)
    c._manual_pending = None
    c._current_window = None
    c._current_session = None
    c._sample_index = 0
    c._idle_ticks = 0
    return c


def test_activity_level_formula():
    c = _controller()
    mock_db = MagicMock()
    # 1050 keystrokes, 0 clicks: score = 1050 / 150 = 7.0
    sample = MagicMock()
    sample.keystrokes = 1050
    sample.mouse_clicks = 0
    mock_db.query.return_value.filter.return_value.all.return_value = [sample]
    result = c._compute_activity_level("test-id", mock_db)
    assert result == 7


def test_activity_level_max_clamp():
    c = _controller()
    mock_db = MagicMock()
    # Very high: 3000 keystrokes → score = 20 → clamped to 10
    sample = MagicMock(keystrokes=3000, mouse_clicks=0)
    mock_db.query.return_value.filter.return_value.all.return_value = [sample]
    assert c._compute_activity_level("x", mock_db) == 10


def test_activity_level_zero():
    c = _controller()
    mock_db = MagicMock()
    sample = MagicMock(keystrokes=0, mouse_clicks=0)
    mock_db.query.return_value.filter.return_value.all.return_value = [sample]
    assert c._compute_activity_level("x", mock_db) == 0


def test_start_requires_contract_id(monkeypatch):
    monkeypatch.setattr(config, "contract_id", "")
    c = _controller()
    with pytest.raises(RuntimeError, match="No contract configured"):
        c.start_tracking()


def test_manual_override_sets_flag():
    c = _controller()
    mock_window = MagicMock()
    mock_window.id = "win-id"
    mock_window.is_manual = False
    mock_window.manual_reason = None

    mock_session = MagicMock()
    mock_session.query.return_value.filter.return_value.first.return_value = mock_window

    c._current_window = MagicMock()
    c._current_window.id = "win-id"

    with patch("tracker.controller.SessionLocal", return_value=mock_session):
        c.set_manual_override("Watching a tutorial")

    assert mock_window.is_manual is True
    assert mock_window.manual_reason == "Watching a tutorial"
