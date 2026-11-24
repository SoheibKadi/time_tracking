import uuid
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel

from app.models.window import WindowStatus


class ActivitySampleIn(BaseModel):
    sample_index: int
    keystrokes: int
    mouse_clicks: int
    mouse_distance_px: int
    sampled_at: datetime


class ActivitySampleOut(ActivitySampleIn):
    id: uuid.UUID
    window_id: uuid.UUID

    model_config = {"from_attributes": True}


class WindowCreate(BaseModel):
    session_id: uuid.UUID
    started_at: datetime
    ended_at: datetime
    activity_level: Optional[int] = None
    is_manual: bool = False
    manual_reason: Optional[str] = None
    activity_samples: List[ActivitySampleIn] = []


class WindowOut(BaseModel):
    id: uuid.UUID
    session_id: uuid.UUID
    started_at: datetime
    ended_at: datetime
    activity_level: Optional[int]
    is_manual: bool
    manual_reason: Optional[str]
    status: WindowStatus
    disputed_at: Optional[datetime]
    dispute_reason: Optional[str]
    resolved_at: Optional[datetime]

    model_config = {"from_attributes": True}


class DisputeRequest(BaseModel):
    reason: Optional[str] = None


class DisputeResolve(BaseModel):
    accept: bool   # True = accept dispute (exclude from billing), False = reject
