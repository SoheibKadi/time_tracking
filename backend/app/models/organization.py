import uuid
from sqlalchemy import Column, String, Text, Integer, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import Base


class Organization(Base):
    __tablename__ = "organizations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    contracts = relationship("Contract", back_populates="organization")


class FreelancerProfile(Base):
    __tablename__ = "freelancer_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), unique=True, nullable=False)
    company_name = Column(String(255))
    address = Column(Text)
    tax_id = Column(String(100))
    tax_label = Column(String(20), default="VAT")
    logo_storage_key = Column(String(500))
    payment_instructions = Column(Text)
    invoice_prefix = Column(String(20), nullable=False, default="INV")
    next_invoice_number = Column(Integer, nullable=False, default=1)

    user = relationship("User", back_populates="freelancer_profile")
