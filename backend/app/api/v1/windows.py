import uuid
from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.deps import get_db, get_current_user
from app.models import User, WorkSession, TimeWindow, ActivitySample, WindowStatus
from app.schemas import WindowCreate, WindowOut, DisputeResolve

router = APIRouter(prefix="/windows", tags=["windows"])


@router.post("", response_model=WindowOut, status_code=201)
def submit_window(body: WindowCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    session = db.query(WorkSession).filter(WorkSession.id == body.session_id, WorkSession.worker_id == user.id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    window = TimeWindow(
        session_id=body.session_id,
        started_at=body.started_at,
        ended_at=body.ended_at,
        activity_level=body.activity_level,
        is_manual=body.is_manual,
        manual_reason=body.manual_reason,
    )
    db.add(window)
    db.flush()

    for sample in body.activity_samples:
        db.add(ActivitySample(
            window_id=window.id,
            sample_index=sample.sample_index,
            keystrokes=sample.keystrokes,
            mouse_clicks=sample.mouse_clicks,
            mouse_distance_px=sample.mouse_distance_px,
            sampled_at=sample.sampled_at,
        ))

    db.commit()
    db.refresh(window)
    return window


@router.get("/contract/{contract_id}", response_model=List[WindowOut])
def list_windows(
    contract_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return (
        db.query(TimeWindow)
        .join(WorkSession)
        .filter(WorkSession.contract_id == contract_id, WorkSession.worker_id == user.id)
        .order_by(TimeWindow.started_at.desc())
        .all()
    )


@router.patch("/{window_id}/dispute/resolve", response_model=WindowOut)
def resolve_dispute(
    window_id: uuid.UUID,
    body: DisputeResolve,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    window = (
        db.query(TimeWindow)
        .join(WorkSession)
        .filter(TimeWindow.id == window_id, WorkSession.worker_id == user.id)
        .first()
    )
    if not window:
        raise HTTPException(status_code=404, detail="Window not found")
    if window.status != WindowStatus.disputed:
        raise HTTPException(status_code=400, detail="Window is not in disputed state")

    window.status = WindowStatus.accepted_dispute if body.accept else WindowStatus.rejected_dispute
    window.resolved_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(window)
    return window
