import uuid
import enum
from sqlalchemy import Column, String, DateTime, Enum as SAEnum, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import Base


class UserRole(str, enum.Enum):
    worker = "worker"
    admin = "admin"


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(SAEnum(UserRole), nullable=False, default=UserRole.worker)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    freelancer_profile = relationship("FreelancerProfile", back_populates="user", uselist=False)
    contracts = relationship("Contract", back_populates="worker", foreign_keys="Contract.worker_id")
    work_sessions = relationship("WorkSession", back_populates="worker")
