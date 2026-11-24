from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import SessionLocal
from app.api.v1.router import api_router, share_router
from app.models import User, Organization, FreelancerProfile, UserRole
from app.services.auth import hash_password


@asynccontextmanager
async def lifespan(app: FastAPI):
    _seed_admin()
    yield


def _seed_admin() -> None:
    """Create the first admin user and their org if they don't exist yet."""
    db = SessionLocal()
    try:
        if db.query(User).filter(User.email == settings.FIRST_ADMIN_EMAIL).first():
            return
        admin = User(
            email=settings.FIRST_ADMIN_EMAIL,
            name=settings.FIRST_ADMIN_NAME,
            password_hash=hash_password(settings.FIRST_ADMIN_PASSWORD),
            role=UserRole.admin,
        )
        db.add(admin)
        db.flush()
        org = Organization(name=f"{admin.name}'s Organization", owner_id=admin.id)
        db.add(org)
        profile = FreelancerProfile(user_id=admin.id, invoice_prefix="INV")
        db.add(profile)
        db.commit()
    finally:
        db.close()


app = FastAPI(title="Time Tracker API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/v1")
app.include_router(share_router)


@app.get("/health")
def health():
    return {"status": "ok"}
