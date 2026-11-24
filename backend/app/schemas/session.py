import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class SessionCreate(BaseModel):
    contract_id: uuid.UUID
    memo: Optional[str] = None


class SessionUpdate(BaseModel):
    action: str   # "pause" | "stop"
    memo: Optional[str] = None


class SessionOut(BaseModel):
    id: uuid.UUID
    contract_id: uuid.UUID
    started_at: datetime
    ended_at: Optional[datetime]
    memo: Optional[str]

    model_config = {"from_attributes": True}
