import uuid
from sqlalchemy import Column, SmallInteger, Integer, BigInteger, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import Base


class ActivitySample(Base):
    __tablename__ = "activity_samples"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    window_id = Column(UUID(as_uuid=True), ForeignKey("time_windows.id"), nullable=False, index=True)
    sample_index = Column(SmallInteger, nullable=False)
    keystrokes = Column(Integer, nullable=False, default=0)
    mouse_clicks = Column(Integer, nullable=False, default=0)
    mouse_distance_px = Column(BigInteger, nullable=False, default=0)
    sampled_at = Column(DateTime(timezone=True), nullable=False)

    window = relationship("TimeWindow", back_populates="activity_samples")
