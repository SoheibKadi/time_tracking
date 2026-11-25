"""Suite 7 — Invoicing (10 tests)."""
import uuid
from datetime import date, datetime, timezone, timedelta

import pytest

from tests.backend.conftest import make_window_in_db
from app.models import WindowStatus


def _create_invoice(client, contract_id, headers, **kwargs):
    today = date.today()
    payload = {
        "contract_id": contract_id,
        "period_start": str(date(today.year, today.month, 1)),
        "period_end": str(today),
        "tax_rate": "0",
        **kwargs,
    }
    return client.post("/v1/invoices", headers=headers, json=payload)


def test_create_invoice_calculates_hours(client, contract, session_obj, worker_headers, db):
    # 2 non-excluded windows of 10 min each = ~0.33 hrs
    make_window_in_db(db, session_obj["id"])
    make_window_in_db(db, session_obj["id"])
    resp = _create_invoice(client, contract["id"], worker_headers)
    assert resp.status_code == 201
    body = resp.json()
    assert float(body["total_hours"]) > 0
    assert float(body["subtotal"]) > 0
    assert len(body["line_items"]) == 1


def test_invoice_excludes_deleted_windows(client, contract, session_obj, worker_headers, db):
    make_window_in_db(db, session_obj["id"], status=WindowStatus.deleted)
    resp = _create_invoice(client, contract["id"], worker_headers)
    assert resp.status_code == 201
    assert float(resp.json()["total_hours"]) == 0.0


def test_invoice_excludes_accepted_disputes(client, contract, session_obj, worker_headers, db):
    make_window_in_db(db, session_obj["id"], status=WindowStatus.accepted_dispute)
    resp = _create_invoice(client, contract["id"], worker_headers)
    assert float(resp.json()["total_hours"]) == 0.0


def test_invoice_includes_rejected_disputes(client, contract, session_obj, worker_headers, db):
    make_window_in_db(db, session_obj["id"], status=WindowStatus.rejected_dispute)
    resp = _create_invoice(client, contract["id"], worker_headers)
    assert float(resp.json()["total_hours"]) > 0.0


def test_invoice_number_increments(client, contract, worker_headers):
    r1 = _create_invoice(client, contract["id"], worker_headers)
    r2 = _create_invoice(client, contract["id"], worker_headers)
    assert r1.json()["invoice_number"] == "INV-0001"
    assert r2.json()["invoice_number"] == "INV-0002"


def test_invoice_tax_calculation(client, contract, session_obj, worker_headers, db):
    make_window_in_db(db, session_obj["id"])
    resp = _create_invoice(client, contract["id"], worker_headers, tax_rate="10")
    assert resp.status_code == 201
    body = resp.json()
    subtotal = float(body["subtotal"])
    tax = float(body["tax_amount"])
    total = float(body["total"])
    assert pytest.approx(tax, rel=1e-2) == subtotal * 0.10
    assert pytest.approx(total, rel=1e-2) == subtotal + tax


def test_invoice_zero_tax(client, contract, worker_headers):
    resp = _create_invoice(client, contract["id"], worker_headers, tax_rate="0")
    body = resp.json()
    assert float(body["tax_amount"]) == 0.0
    assert float(body["total"]) == float(body["subtotal"])


def test_update_invoice_status(client, contract, worker_headers):
    inv_id = _create_invoice(client, contract["id"], worker_headers).json()["id"]
    r1 = client.patch(f"/v1/invoices/{inv_id}", headers=worker_headers, json={"status": "sent"})
    assert r1.json()["status"] == "sent"
    r2 = client.patch(f"/v1/invoices/{inv_id}", headers=worker_headers, json={"status": "paid"})
    assert r2.json()["status"] == "paid"


def test_download_pdf(client, contract, worker_headers):
    inv_id = _create_invoice(client, contract["id"], worker_headers).json()["id"]
    resp = client.get(f"/v1/invoices/{inv_id}/pdf", headers=worker_headers)
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/pdf"
    assert resp.content.startswith(b"%PDF")


def test_invoice_wrong_owner(client, worker2, worker2_headers, contract, worker_headers):
    inv_id = _create_invoice(client, contract["id"], worker_headers).json()["id"]
    resp = client.get(f"/v1/invoices/{inv_id}/pdf", headers=worker2_headers)
    assert resp.status_code == 404
