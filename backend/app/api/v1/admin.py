import secrets
import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from app.deps import get_db, require_admin
from app.models import User, AuditLog, Organization, FreelancerProfile, UserRole
from app.services.auth import hash_password

router = APIRouter(prefix="/admin", tags=["admin"])


# ── Schemas ───────────────────────────────────────────────────────────────────

class UserOut(BaseModel):
    id: uuid.UUID
    email: str
    name: str
    role: str
    is_active: bool

    model_config = {"from_attributes": True}


class UserUpdate(BaseModel):
    is_active: Optional[bool] = None


class InviteRequest(BaseModel):
    email: EmailStr
    name: str
    role: str = "worker"


# ── Users ─────────────────────────────────────────────────────────────────────

@router.get("/users", response_model=List[UserOut])
def list_users(_: User = Depends(require_admin), db: Session = Depends(get_db)):
    return db.query(User).order_by(User.created_at.desc()).all()


@router.patch("/users/{user_id}", response_model=UserOut)
def update_user(
    user_id: uuid.UUID,
    body: UserUpdate,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if body.is_active is not None:
        user.is_active = body.is_active
        _audit(db, admin.id, "user.deactivate" if not body.is_active else "user.reactivate",
               f"user_id={user_id}")
    db.commit()
    db.refresh(user)
    return user


@router.post("/users/invite", status_code=201)
def invite_user(
    body: InviteRequest,
    request: Request,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    if db.query(User).filter(User.email == body.email).first():
        raise HTTPException(status_code=409, detail="Email already registered")

    temp_password = secrets.token_urlsafe(12)
    role = UserRole.admin if body.role == "admin" else UserRole.worker
    user = User(
        email=body.email,
        name=body.name,
        password_hash=hash_password(temp_password),
        role=role,
    )
    db.add(user)
    db.flush()

    org = Organization(name=f"{user.name}'s Organization", owner_id=user.id)
    db.add(org)
    db.add(FreelancerProfile(user_id=user.id, invoice_prefix="INV"))

    _audit(db, admin.id, "user.invite", f"email={body.email} role={body.role}",
           ip=request.client.host if request.client else None)
    db.commit()

    return {"id": str(user.id), "temp_password": temp_password}


# ── Audit log ─────────────────────────────────────────────────────────────────

@router.get("/audit")
def get_audit(_: User = Depends(require_admin), db: Session = Depends(get_db)):
    logs = db.query(AuditLog).order_by(AuditLog.created_at.desc()).limit(200).all()
    return [
        {
            "id": str(log.id),
            "user_id": str(log.user_id) if log.user_id else None,
            "share_token": str(log.share_token) if log.share_token else None,
            "action": log.action,
            "details": log.details,
            "ip_address": log.ip_address,
            "created_at": log.created_at.isoformat(),
        }
        for log in logs
    ]


# ── Helper ────────────────────────────────────────────────────────────────────

def _audit(db: Session, user_id, action: str, details: str = "", ip: str = None):
    db.add(AuditLog(user_id=user_id, action=action, details=details, ip_address=ip))
