import uuid
from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.deps import get_db, get_current_user
from app.models import User, Contract, WorkSession
from app.schemas import SessionCreate, SessionUpdate, SessionOut

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.post("", response_model=SessionOut, status_code=201)
def start_session(body: SessionCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    contract = db.query(Contract).filter(Contract.id == body.contract_id, Contract.worker_id == user.id).first()
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    if contract.status != "active":
        raise HTTPException(status_code=400, detail="Contract is not active")

    session = WorkSession(contract_id=contract.id, worker_id=user.id, memo=body.memo)
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


@router.patch("/{session_id}", response_model=SessionOut)
def update_session(
    session_id: uuid.UUID,
    body: SessionUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session = db.query(WorkSession).filter(WorkSession.id == session_id, WorkSession.worker_id == user.id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if body.action not in ("pause", "stop"):
        raise HTTPException(status_code=400, detail="action must be 'pause' or 'stop'")

    if body.action == "stop" and session.ended_at is None:
        session.ended_at = datetime.now(timezone.utc)
    if body.memo is not None:
        session.memo = body.memo

    db.commit()
    db.refresh(session)
    return session


@router.get("/contract/{contract_id}", response_model=List[SessionOut])
def list_sessions(
    contract_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    contract = db.query(Contract).filter(Contract.id == contract_id, Contract.worker_id == user.id).first()
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    return db.query(WorkSession).filter(WorkSession.contract_id == contract_id).order_by(WorkSession.started_at.desc()).all()
