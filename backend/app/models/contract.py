import uuid
import enum
from sqlalchemy import Column, String, Numeric, Integer, DateTime, ForeignKey, Enum as SAEnum, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import Base


class ContractStatus(str, enum.Enum):
    active = "active"
    paused = "paused"
    closed = "closed"


class Contract(Base):
    __tablename__ = "contracts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    worker_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    title = Column(String(255), nullable=False)
    hourly_rate = Column(Numeric(10, 2), nullable=False)
    weekly_hour_limit = Column(Numeric(5, 2))
    screenshot_interval_min = Column(Integer, nullable=False, default=10)
    status = Column(SAEnum(ContractStatus), nullable=False, default=ContractStatus.active)
    share_token = Column(UUID(as_uuid=True), nullable=False, default=uuid.uuid4, unique=True, index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    organization = relationship("Organization", back_populates="contracts")
    worker = relationship("User", back_populates="contracts", foreign_keys=[worker_id])
    client_profile = relationship("ClientProfile", back_populates="contract", uselist=False)
    work_sessions = relationship("WorkSession", back_populates="contract")
    invoices = relationship("Invoice", back_populates="contract")


class ClientProfile(Base):
    __tablename__ = "client_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    contract_id = Column(UUID(as_uuid=True), ForeignKey("contracts.id"), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    company_name = Column(String(255))
    billing_email = Column(String(255))
    billing_address = Column(String(500))

    contract = relationship("Contract", back_populates="client_profile")
