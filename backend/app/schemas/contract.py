import uuid
from decimal import Decimal
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr

from app.models.contract import ContractStatus


class ClientProfileIn(BaseModel):
    name: str
    company_name: Optional[str] = None
    billing_email: Optional[EmailStr] = None
    billing_address: Optional[str] = None


class ClientProfileOut(ClientProfileIn):
    id: uuid.UUID

    model_config = {"from_attributes": True}


class ContractCreate(BaseModel):
    title: str
    hourly_rate: Decimal
    weekly_hour_limit: Optional[Decimal] = None
    screenshot_interval_min: int = 10
    client: ClientProfileIn


class ContractUpdate(BaseModel):
    title: Optional[str] = None
    hourly_rate: Optional[Decimal] = None
    weekly_hour_limit: Optional[Decimal] = None
    screenshot_interval_min: Optional[int] = None
    status: Optional[ContractStatus] = None


class ContractOut(BaseModel):
    id: uuid.UUID
    title: str
    hourly_rate: Decimal
    weekly_hour_limit: Optional[Decimal]
    screenshot_interval_min: int
    status: ContractStatus
    share_token: uuid.UUID
    created_at: datetime
    client_profile: Optional[ClientProfileOut]

    model_config = {"from_attributes": True}


class FreelancerProfileUpdate(BaseModel):
    company_name: Optional[str] = None
    address: Optional[str] = None
    tax_id: Optional[str] = None
    tax_label: Optional[str] = None
    payment_instructions: Optional[str] = None
    invoice_prefix: Optional[str] = None


class FreelancerProfileOut(FreelancerProfileUpdate):
    id: uuid.UUID
    next_invoice_number: int

    model_config = {"from_attributes": True}
