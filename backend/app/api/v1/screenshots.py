import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Response
from sqlalchemy.orm import Session

from app.deps import get_db, get_current_user
from app.models import User, TimeWindow, Screenshot, WorkSession, WindowStatus
from app.schemas import ScreenshotOut
from app.services.storage import upload_screenshot, get_presigned_url, delete_object

router = APIRouter(prefix="/screenshots", tags=["screenshots"])

GRACE_PERIOD_SECONDS = 60


@router.post("", response_model=ScreenshotOut, status_code=201)
def upload(
    window_id: uuid.UUID = Form(...),
    captured_at: datetime = Form(...),
    file: UploadFile = File(...),
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

    data = file.file.read()
    key = f"screenshots/{user.id}/{window_id}.png"
    storage_key, thumb_key, sha256 = upload_screenshot(data, key)

    existing = db.query(Screenshot).filter(Screenshot.window_id == window_id).first()
    if existing:
        raise HTTPException(status_code=409, detail="Screenshot already exists for this window")

    screenshot = Screenshot(
        window_id=window_id,
        captured_at=captured_at,
        storage_key=storage_key,
        sha256=sha256,
        thumbnail_key=thumb_key,
    )
    db.add(screenshot)
    db.commit()
    db.refresh(screenshot)
    return screenshot


@router.get("/{screenshot_id}/image")
def get_image(screenshot_id: uuid.UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    screenshot = (
        db.query(Screenshot)
        .join(TimeWindow)
        .join(WorkSession)
        .filter(Screenshot.id == screenshot_id, WorkSession.worker_id == user.id)
        .first()
    )
    if not screenshot or screenshot.deleted_at:
        raise HTTPException(status_code=404, detail="Screenshot not found")
    url = get_presigned_url(screenshot.storage_key)
    return {"url": url}


@router.delete("/{screenshot_id}", status_code=204)
def delete_screenshot(
    screenshot_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    screenshot = (
        db.query(Screenshot)
        .join(TimeWindow)
        .join(WorkSession)
        .filter(Screenshot.id == screenshot_id, WorkSession.worker_id == user.id)
        .first()
    )
    if not screenshot or screenshot.deleted_at:
        raise HTTPException(status_code=404, detail="Screenshot not found")

    age = (datetime.now(timezone.utc) - screenshot.captured_at.replace(tzinfo=timezone.utc)).total_seconds()
    if age > GRACE_PERIOD_SECONDS:
        raise HTTPException(status_code=400, detail="Grace period expired")

    screenshot.deleted_at = datetime.now(timezone.utc)
    screenshot.window.status = WindowStatus.deleted
    delete_object(screenshot.storage_key)
    if screenshot.thumbnail_key:
        delete_object(screenshot.thumbnail_key)

    db.commit()
    return Response(status_code=204)
