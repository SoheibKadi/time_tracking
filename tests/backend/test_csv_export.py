"""Suite 10 — CSV export (4 tests)."""
import io
import csv
from datetime import date, datetime, timezone, timedelta

import pytest

from tests.backend.conftest import make_window_in_db
from app.models import WindowStatus


EXPECTED_HEADERS = [
    "date", "session_id", "window_start", "window_end", "duration_min",
    "activity_level", "is_manual", "manual_reason", "status",
    "keystrokes", "mouse_clicks", "mouse_distance_px",
]


def _export(client, contract_id, headers, **params):
    today = date.today()
    return client.get(
        f"/v1/contracts/{contract_id}/export",
        headers=headers,
        params={
            "from_date": str(date(today.year, today.month, 1)),
            "to_date": str(today),
            **params,
        },
    )


def _parse_csv(resp):
    return list(csv.DictReader(io.StringIO(resp.text)))


def test_csv_has_correct_headers(client, contract, session_obj, worker_headers, db):
    make_window_in_db(db, session_obj["id"])
    resp = _export(client, contract["id"], worker_headers)
    assert resp.status_code == 200
    assert "text/csv" in resp.headers["content-type"]
    rows = _parse_csv(resp)
    assert list(rows[0].keys()) == EXPECTED_HEADERS


def test_csv_rows_match_windows(client, contract, session_obj, worker_headers, db):
    make_window_in_db(db, session_obj["id"])
    make_window_in_db(db, session_obj["id"])
    resp = _export(client, contract["id"], worker_headers)
    rows = _parse_csv(resp)
    assert len(rows) == 2


def test_csv_date_range_filter(client, contract, session_obj, worker_headers, db):
    # Window from last month should be excluded
    last_month_start = datetime.now(timezone.utc) - timedelta(days=40)
    from app.models import TimeWindow
    import uuid
    old = TimeWindow(
        session_id=uuid.UUID(session_obj["id"]),
        started_at=last_month_start,
        ended_at=last_month_start + timedelta(minutes=10),
        activity_level=5,
    )
    db.add(old)
    db.commit()
    make_window_in_db(db, session_obj["id"])  # this month

    today = date.today()
    resp = client.get(
        f"/v1/contracts/{contract['id']}/export",
        headers=worker_headers,
        params={
            "from_date": str(date(today.year, today.month, 1)),
            "to_date": str(today),
        },
    )
    rows = _parse_csv(resp)
    assert len(rows) == 1  # only current month window


def test_csv_empty_contract(client, contract, worker_headers):
    resp = _export(client, contract["id"], worker_headers)
    assert resp.status_code == 200
    rows = _parse_csv(resp)
    assert len(rows) == 0  # headers only, no data rows
