"""Local SQLite models for the desktop agent."""
import uuid
import enum
from datetime import datetime

from sqlalchemy import Column, String, Integer, BigInteger, Boolean, Text, DateTime, SmallInteger, Enum as SAEnum
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class SyncStatus(str, enum.Enum):
    pending = "pending"
    uploaded = "uploaded"
    failed = "failed"


class LocalWindow(Base):
    """One 10-minute work window stored locally until synced."""
    __tablename__ = "windows"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String(36), nullable=False)
    contract_id = Column(String(36), nullable=False)
    started_at = Column(DateTime, nullable=False)
    ended_at = Column(DateTime, nullable=False)
    activity_level = Column(SmallInteger)
    is_manual = Column(Boolean, nullable=False, default=False)
    manual_reason = Column(Text)
    sync_status = Column(SAEnum(SyncStatus), nullable=False, default=SyncStatus.pending)
    remote_id = Column(String(36))   # server-assigned UUID after upload


class LocalActivitySample(Base):
    """One 60-second activity sample."""
    __tablename__ = "activity_samples"

    id = Column(Integer, primary_key=True, autoincrement=True)
    window_id = Column(String(36), nullable=False, index=True)
    sample_index = Column(SmallInteger, nullable=False)
    keystrokes = Column(Integer, nullable=False, default=0)
    mouse_clicks = Column(Integer, nullable=False, default=0)
    mouse_distance_px = Column(BigInteger, nullable=False, default=0)
    sampled_at = Column(DateTime, nullable=False)


class LocalScreenshot(Base):
    """Screenshot metadata and local spool path."""
    __tablename__ = "screenshots"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    window_id = Column(String(36), nullable=False, unique=True)
    captured_at = Column(DateTime, nullable=False)
    local_path = Column(String(500), nullable=False)
    sha256 = Column(String(64), nullable=False)
    sync_status = Column(SAEnum(SyncStatus), nullable=False, default=SyncStatus.pending)


class LocalSession(Base):
    """Current or recent work session."""
    __tablename__ = "sessions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    contract_id = Column(String(36), nullable=False)
    remote_session_id = Column(String(36))
    started_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    ended_at = Column(DateTime)
    is_active = Column(Boolean, nullable=False, default=True)
