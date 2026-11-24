import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class ScreenshotOut(BaseModel):
    id: uuid.UUID
    window_id: uuid.UUID
    captured_at: datetime
    sha256: str
    deleted_at: Optional[datetime]

    model_config = {"from_attributes": True}
