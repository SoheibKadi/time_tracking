from fastapi import APIRouter

from app.api.v1 import auth, register, contracts, sessions, windows, screenshots, share, invoices, admin, blocklist

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(register.router)
api_router.include_router(contracts.router)
api_router.include_router(contracts.profile_router)
api_router.include_router(sessions.router)
api_router.include_router(windows.router)
api_router.include_router(screenshots.router)
api_router.include_router(invoices.router)
api_router.include_router(admin.router)
api_router.include_router(blocklist.router)

share_router = APIRouter()
share_router.include_router(share.router)
