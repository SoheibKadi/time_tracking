import uuid
import enum
from sqlalchemy import Column, String, SmallInteger, Boolean, Text, DateTime, ForeignKey, Enum as SAEnum, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import Base


class WindowStatus(str, enum.Enum):
    submitted = "submitted"
    deleted = "deleted"
    disputed = "disputed"
    accepted_dispute = "accepted_dispute"
    rejected_dispute = "rejected_dispute"


class TimeWindow(Base):
    __tablename__ = "time_windows"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("work_sessions.id"), nullable=False)
    started_at = Column(DateTime(timezone=True), nullable=False)
    ended_at = Column(DateTime(timezone=True), nullable=False)
    activity_level = Column(SmallInteger)   # 0-10; NULL when is_manual=True
    is_manual = Column(Boolean, nullable=False, default=False)
    manual_reason = Column(Text)
    status = Column(SAEnum(WindowStatus), nullable=False, default=WindowStatus.submitted)
    disputed_at = Column(DateTime(timezone=True))
    dispute_reason = Column(Text)
    resolved_at = Column(DateTime(timezone=True))

    session = relationship("WorkSession", back_populates="windows")
    screenshot = relationship("Screenshot", back_populates="window", uselist=False)
    activity_samples = relationship("ActivitySample", back_populates="window")
