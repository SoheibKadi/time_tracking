import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import Base


class Screenshot(Base):
    __tablename__ = "screenshots"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    window_id = Column(UUID(as_uuid=True), ForeignKey("time_windows.id"), nullable=False, unique=True)
    captured_at = Column(DateTime(timezone=True), nullable=False)
    storage_key = Column(String(500), nullable=False)
    sha256 = Column(String(64), nullable=False)
    thumbnail_key = Column(String(500))
    deleted_at = Column(DateTime(timezone=True))

    window = relationship("TimeWindow", back_populates="screenshot")
