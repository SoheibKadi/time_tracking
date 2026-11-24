import uuid
import smtplib
import email.message
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.deps import get_db
from app.models import Contract, WorkSession, TimeWindow, Screenshot, WindowStatus
from app.schemas import WindowOut, DisputeRequest, ScreenshotOut
from app.services.storage import get_presigned_url
from app.config import settings

router = APIRouter(prefix="/share", tags=["share"])


def _get_contract_by_token(token: uuid.UUID, db: Session) -> Contract:
    c = db.query(Contract).filter(Contract.share_token == token).first()
    if not c:
        raise HTTPException(status_code=404, detail="Invalid share link")
    return c


def _billable_hours(windows: list) -> float:
    billable = [
        w for w in windows
        if w.status not in (WindowStatus.deleted, WindowStatus.accepted_dispute)
    ]
    total = sum((w.ended_at - w.started_at).total_seconds() for w in billable)
    return round(total / 3600, 2)


@router.get("/{token}")
def client_view(token: uuid.UUID, db: Session = Depends(get_db)):
    contract = _get_contract_by_token(token, db)
    windows = (
        db.query(TimeWindow)
        .join(WorkSession)
        .filter(WorkSession.contract_id == contract.id)
        .order_by(TimeWindow.started_at.desc())
        .all()
    )
    return {
        "contract_title": contract.title,
        "hourly_rate": float(contract.hourly_rate),
        "billable_hours": _billable_hours(windows),
        "windows": [_window_to_dict(w, db) for w in windows],
        "refreshed_at": datetime.now(timezone.utc).isoformat(),
    }


def _window_to_dict(w: TimeWindow, db: Session) -> dict:
    screenshot = db.query(Screenshot).filter(Screenshot.window_id == w.id, Screenshot.deleted_at.is_(None)).first()
    return {
        "id": str(w.id),
        "started_at": w.started_at.isoformat(),
        "ended_at": w.ended_at.isoformat(),
        "duration_minutes": round((w.ended_at - w.started_at).total_seconds() / 60, 1),
        "activity_level": w.activity_level,
        "is_manual": w.is_manual,
        "manual_reason": w.manual_reason,
        "status": w.status.value,
        "disputed_at": w.disputed_at.isoformat() if w.disputed_at else None,
        "dispute_reason": w.dispute_reason,
        "resolved_at": w.resolved_at.isoformat() if w.resolved_at else None,
        "has_screenshot": screenshot is not None,
        "screenshot_id": str(screenshot.id) if screenshot else None,
        "thumbnail_url": get_presigned_url(screenshot.thumbnail_key, expires=3600) if screenshot and screenshot.thumbnail_key else None,
    }


@router.get("/{token}/screenshots/{screenshot_id}")
def client_screenshot(token: uuid.UUID, screenshot_id: uuid.UUID, db: Session = Depends(get_db)):
    contract = _get_contract_by_token(token, db)
    screenshot = (
        db.query(Screenshot)
        .join(TimeWindow)
        .join(WorkSession)
        .filter(
            Screenshot.id == screenshot_id,
            WorkSession.contract_id == contract.id,
            Screenshot.deleted_at.is_(None),
        )
        .first()
    )
    if not screenshot:
        raise HTTPException(status_code=404, detail="Screenshot not found")
    return {"url": get_presigned_url(screenshot.storage_key, expires=3600)}


@router.patch("/{token}/windows/{window_id}/dispute")
def dispute_window(token: uuid.UUID, window_id: uuid.UUID, body: DisputeRequest, db: Session = Depends(get_db)):
    contract = _get_contract_by_token(token, db)
    window = (
        db.query(TimeWindow)
        .join(WorkSession)
        .filter(TimeWindow.id == window_id, WorkSession.contract_id == contract.id)
        .first()
    )
    if not window:
        raise HTTPException(status_code=404, detail="Window not found")
    if window.status not in (WindowStatus.submitted,):
        raise HTTPException(status_code=400, detail=f"Cannot dispute a window with status '{window.status.value}'")

    window.status = WindowStatus.disputed
    window.disputed_at = datetime.now(timezone.utc)
    window.dispute_reason = body.reason
    db.commit()

    _notify_worker_dispute(contract, window)
    return {"detail": "Dispute submitted"}


def _notify_worker_dispute(contract: Contract, window: TimeWindow) -> None:
    if not settings.SMTP_HOST:
        return
    worker = contract.worker
    msg = email.message.EmailMessage()
    msg["Subject"] = f"[Time Tracker] Dispute on contract '{contract.title}'"
    msg["From"] = settings.SMTP_FROM
    msg["To"] = worker.email
    msg.set_content(
        f"Hi {worker.name},\n\n"
        f"Your client has disputed the time window "
        f"{window.started_at.strftime('%Y-%m-%d %H:%M')} – {window.ended_at.strftime('%H:%M')} UTC"
        f" on contract '{contract.title}'.\n\n"
        f"Reason: {window.dispute_reason or '(none provided)'}\n\n"
        f"Log in to your dashboard to accept or reject the dispute."
    )
    try:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as smtp:
            if settings.SMTP_USER:
                smtp.starttls()
                smtp.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            smtp.send_message(msg)
    except Exception:
        pass  # Email is best-effort; never block the dispute action
