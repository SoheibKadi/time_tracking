import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.deps import get_db, get_current_user
from app.models import User, Organization, Contract, ClientProfile, FreelancerProfile
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
