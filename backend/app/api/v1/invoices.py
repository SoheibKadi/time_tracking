import uuid
from datetime import date
from decimal import Decimal
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from app.deps import get_db, get_current_user
from app.models import User, Contract, WorkSession, TimeWindow, WindowStatus, FreelancerProfile, Invoice, InvoiceLineItem, InvoiceStatus
from app.schemas import InvoiceCreate, InvoiceUpdate, InvoiceOut
from app.services.pdf import render_invoice_pdf

router = APIRouter(prefix="/invoices", tags=["invoices"])


def _get_or_404(invoice_id: uuid.UUID, user: User, db: Session) -> Invoice:
    inv = (
        db.query(Invoice)
        .join(Contract)
        .filter(Invoice.id == invoice_id, Contract.worker_id == user.id)
        .first()
    )
    if not inv:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return inv


@router.post("", response_model=InvoiceOut, status_code=201)
def create_invoice(body: InvoiceCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    contract = db.query(Contract).filter(Contract.id == body.contract_id, Contract.worker_id == user.id).first()
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")

    # Collect billable windows in the period
    windows = (
        db.query(TimeWindow)
        .join(WorkSession)
        .filter(
            WorkSession.contract_id == contract.id,
            TimeWindow.started_at >= body.period_start,
            TimeWindow.ended_at <= body.period_end,
            TimeWindow.status.notin_([WindowStatus.deleted, WindowStatus.accepted_dispute]),
        )
        .all()
    )

    total_seconds = sum((w.ended_at - w.started_at).total_seconds() for w in windows)
    total_hours = Decimal(str(round(total_seconds / 3600, 2)))
    subtotal = (total_hours * contract.hourly_rate).quantize(Decimal("0.01"))
    tax_amount = (subtotal * body.tax_rate / 100).quantize(Decimal("0.01"))
    total = subtotal + tax_amount

    # Invoice number
    profile = db.query(FreelancerProfile).filter(FreelancerProfile.user_id == user.id).first()
    prefix = profile.invoice_prefix if profile else "INV"
    num = profile.next_invoice_number if profile else 1
    invoice_number = f"{prefix}-{num:04d}"
    if profile:
        profile.next_invoice_number = num + 1

    # Period label for the single line item
    period_label = f"{body.period_start.strftime('%B %Y')}" if body.period_start.month == body.period_end.month else \
        f"{body.period_start.strftime('%b %d')} – {body.period_end.strftime('%b %d, %Y')}"
    description = f"{period_label} — {total_hours} hrs @ ${contract.hourly_rate}/hr"

    invoice = Invoice(
        contract_id=contract.id,
        invoice_number=invoice_number,
        period_start=body.period_start,
        period_end=body.period_end,
        total_hours=total_hours,
        hourly_rate=contract.hourly_rate,
        subtotal=subtotal,
        tax_rate=body.tax_rate,
        tax_amount=tax_amount,
        total=total,
        due_at=body.due_at,
        notes=body.notes,
    )
    db.add(invoice)
    db.flush()

    db.add(InvoiceLineItem(
        invoice_id=invoice.id,
        description=description,
        hours=total_hours,
        rate=contract.hourly_rate,
        amount=subtotal,
    ))

    db.commit()
    db.refresh(invoice)
    return invoice


@router.get("", response_model=List[InvoiceOut])
def list_invoices(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return (
        db.query(Invoice)
        .join(Contract)
        .filter(Contract.worker_id == user.id)
        .order_by(Invoice.issued_at.desc())
        .all()
    )


@router.patch("/{invoice_id}", response_model=InvoiceOut)
def update_invoice(
    invoice_id: uuid.UUID,
    body: InvoiceUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    invoice = _get_or_404(invoice_id, user, db)
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(invoice, field, value)
    db.commit()
    db.refresh(invoice)
    return invoice


@router.get("/{invoice_id}/pdf")
def download_pdf(invoice_id: uuid.UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    invoice = _get_or_404(invoice_id, user, db)
    contract = invoice.contract
    worker = user
    profile = db.query(FreelancerProfile).filter(FreelancerProfile.user_id == user.id).first()

    context = {
        "invoice": invoice,
        "profile": {
            "name": worker.name,
            "email": worker.email,
            "company_name": profile.company_name if profile else None,
            "address": profile.address if profile else None,
            "tax_id": profile.tax_id if profile else None,
            "tax_label": profile.tax_label if profile else "VAT",
            "logo_url": None,
            "payment_instructions": profile.payment_instructions if profile else None,
        },
        "client": contract.client_profile,
        "tracker_url": f"/share/{contract.share_token}",
    }

    pdf_bytes = render_invoice_pdf(context)
    filename = f"{invoice.invoice_number}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
