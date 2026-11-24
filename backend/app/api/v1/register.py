from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from app.deps import get_db
from app.models import User, Organization, FreelancerProfile, UserRole
from app.services.auth import hash_password
from app.config import settings

router = APIRouter(prefix="/auth", tags=["register"])


class RegisterRequest(BaseModel):
    email: EmailStr
    name: str
    password: str


@router.post("/register", status_code=201)
def register(body: RegisterRequest, db: Session = Depends(get_db)):
    if not settings.ALLOW_REGISTRATION:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Registration is disabled")

    if db.query(User).filter(User.email == body.email).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    user = User(
        email=body.email,
        name=body.name,
        password_hash=hash_password(body.password),
        role=UserRole.worker,
    )
    db.add(user)
    db.flush()

    org = Organization(name=f"{user.name}'s Organization", owner_id=user.id)
    db.add(org)
    profile = FreelancerProfile(user_id=user.id, invoice_prefix="INV")
    db.add(profile)
    db.commit()

    return {"detail": "Account created. You can now log in."}
