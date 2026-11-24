import uuid
from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel

from app.models.invoice import InvoiceStatus


class InvoiceCreate(BaseModel):
    contract_id: uuid.UUID
    period_start: date
    period_end: date
    tax_rate: Decimal = Decimal("0")
    due_at: Optional[datetime] = None
    notes: Optional[str] = None


class InvoiceUpdate(BaseModel):
    status: Optional[InvoiceStatus] = None
    tax_rate: Optional[Decimal] = None
    due_at: Optional[datetime] = None
    paid_at: Optional[datetime] = None
    notes: Optional[str] = None


class InvoiceLineItemOut(BaseModel):
    id: uuid.UUID
    description: str
    hours: Decimal
    rate: Decimal
    amount: Decimal

    model_config = {"from_attributes": True}


class InvoiceOut(BaseModel):
    id: uuid.UUID
    contract_id: uuid.UUID
    invoice_number: str
    period_start: date
    period_end: date
    total_hours: Decimal
    hourly_rate: Decimal
    subtotal: Decimal
    tax_rate: Decimal
    tax_amount: Decimal
    total: Decimal
    status: InvoiceStatus
    issued_at: datetime
    due_at: Optional[datetime]
    paid_at: Optional[datetime]
    notes: Optional[str]
    line_items: List[InvoiceLineItemOut] = []

    model_config = {"from_attributes": True}
