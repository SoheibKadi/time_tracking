import csv
import io
import uuid
from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.deps import get_db, get_current_user
from app.models import User, Organization, Contract, ClientProfile, FreelancerProfile, WorkSession, TimeWindow, ActivitySample
from app.schemas import ContractCreate, ContractUpdate, ContractOut, FreelancerProfileUpdate, FreelancerProfileOut

router = APIRouter(prefix="/contracts", tags=["contracts"])


def _get_contract_or_404(contract_id: uuid.UUID, user: User, db: Session) -> Contract:
    c = db.query(Contract).filter(Contract.id == contract_id, Contract.worker_id == user.id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Contract not found")
    return c


@router.get("", response_model=List[ContractOut])
def list_contracts(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(Contract).filter(Contract.worker_id == user.id).all()


@router.post("", response_model=ContractOut, status_code=201)
def create_contract(body: ContractCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Ensure the user has an org; create one if not
    org = db.query(Organization).filter(Organization.owner_id == user.id).first()
    if not org:
        org = Organization(name=f"{user.name}'s Organization", owner_id=user.id)
        db.add(org)
        db.flush()

    contract = Contract(
        org_id=org.id,
        worker_id=user.id,
        title=body.title,
        hourly_rate=body.hourly_rate,
        weekly_hour_limit=body.weekly_hour_limit,
        screenshot_interval_min=body.screenshot_interval_min,
    )
    db.add(contract)
    db.flush()

    client = ClientProfile(
        contract_id=contract.id,
        name=body.client.name,
        company_name=body.client.company_name,
        billing_email=str(body.client.billing_email) if body.client.billing_email else None,
        billing_address=body.client.billing_address,
    )
    db.add(client)
    db.commit()
    db.refresh(contract)
    return contract


@router.get("/{contract_id}", response_model=ContractOut)
def get_contract(contract_id: uuid.UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return _get_contract_or_404(contract_id, user, db)


@router.patch("/{contract_id}", response_model=ContractOut)
def update_contract(
    contract_id: uuid.UUID,
    body: ContractUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    contract = _get_contract_or_404(contract_id, user, db)
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(contract, field, value)
    db.commit()
    db.refresh(contract)
    return contract


@router.post("/{contract_id}/regenerate-token", response_model=ContractOut)
def regenerate_share_token(
    contract_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    contract = _get_contract_or_404(contract_id, user, db)
    contract.share_token = uuid.uuid4()
    db.commit()
    db.refresh(contract)
    return contract


@router.get("/{contract_id}/export")
def export_csv(
    contract_id: uuid.UUID,
    from_date: Optional[date] = Query(None),
    to_date: Optional[date] = Query(None),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    contract = _get_contract_or_404(contract_id, user, db)

    q = (
        db.query(TimeWindow, WorkSession)
        .join(WorkSession, TimeWindow.session_id == WorkSession.id)
        .filter(WorkSession.contract_id == contract.id)
    )
    if from_date:
        q = q.filter(TimeWindow.started_at >= from_date)
    if to_date:
        q = q.filter(TimeWindow.ended_at <= to_date)
    rows = q.order_by(TimeWindow.started_at).all()

    # Aggregate activity per window
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow([
        "date", "session_id", "window_start", "window_end",
        "duration_min", "activity_level", "is_manual", "manual_reason",
        "status", "keystrokes", "mouse_clicks", "mouse_distance_px",
    ])

    for window, session in rows:
        samples = db.query(ActivitySample).filter(ActivitySample.window_id == window.id).all()
        keystrokes = sum(s.keystrokes for s in samples)
        clicks = sum(s.mouse_clicks for s in samples)
        distance = sum(s.mouse_distance_px for s in samples)
        duration = round((window.ended_at - window.started_at).total_seconds() / 60, 1)
        writer.writerow([
            window.started_at.strftime("%Y-%m-%d"),
            str(session.id),
            window.started_at.isoformat(),
            window.ended_at.isoformat(),
            duration,
            window.activity_level if window.activity_level is not None else "",
            window.is_manual,
            window.manual_reason or "",
            window.status.value,
            keystrokes, clicks, distance,
        ])

    buf.seek(0)
    filename = f"{contract.title.replace(' ', '_')}_export.csv"
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ── Freelancer profile ────────────────────────────────────────────────────────

profile_router = APIRouter(prefix="/profile", tags=["profile"])


@profile_router.get("", response_model=FreelancerProfileOut)
def get_profile(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    p = db.query(FreelancerProfile).filter(FreelancerProfile.user_id == user.id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Profile not found")
    return p


@profile_router.put("", response_model=FreelancerProfileOut)
def upsert_profile(
    body: FreelancerProfileUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    p = db.query(FreelancerProfile).filter(FreelancerProfile.user_id == user.id).first()
    if not p:
        p = FreelancerProfile(user_id=user.id)
        db.add(p)
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(p, field, value)
    db.commit()
    db.refresh(p)
    return p
