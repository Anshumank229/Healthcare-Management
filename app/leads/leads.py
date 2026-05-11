from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import SessionLocal
from app.models.user import User
from app.models.lead import Lead, LeadStatus
from app.schemas.lead import LeadCreate, LeadUpdate, LeadResponse
from app.auth.auth import get_current_user

router = APIRouter(prefix="/leads", tags=["Leads"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/", response_model=LeadResponse, status_code=status.HTTP_201_CREATED)
def create_lead(
        lead_data: LeadCreate,
        db: Session = Depends(get_db)
):
    """Public endpoint — anyone can submit a lead (website form, ad, etc.)"""
    lead = Lead(**lead_data.model_dump())
    db.add(lead)
    db.commit()
    db.refresh(lead)
    return lead


@router.get("/", response_model=List[LeadResponse])
def get_leads(
        status: Optional[LeadStatus] = None,
        source: Optional[str] = None,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """Staff/Admin sees all leads. Filter by status or source."""
    query = db.query(Lead)
    if status:
        query = query.filter(Lead.status == status)
    if source:
        query = query.filter(Lead.source == source)
    return query.order_by(Lead.created_at.desc()).all()


@router.get("/{lead_id}", response_model=LeadResponse)
def get_lead(
        lead_id: int,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return lead


@router.put("/{lead_id}", response_model=LeadResponse)
def update_lead(
        lead_id: int,
        lead_data: LeadUpdate,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """Update lead status, add notes, etc."""
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    for field, value in lead_data.model_dump(exclude_unset=True).items():
        setattr(lead, field, value)
    db.commit()
    db.refresh(lead)
    return lead


@router.delete("/{lead_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_lead(
        lead_id: int,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    db.delete(lead)
    db.commit()


@router.get("/stats/summary")
def lead_stats(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """Quick summary for the dashboard."""
    total = db.query(Lead).count()
    new = db.query(Lead).filter(Lead.status == LeadStatus.new).count()
    contacted = db.query(Lead).filter(Lead.status == LeadStatus.contacted).count()
    booked = db.query(Lead).filter(Lead.status == LeadStatus.booked).count()
    lost = db.query(Lead).filter(Lead.status == LeadStatus.lost).count()
    conversion_rate = round((booked / total * 100), 1) if total > 0 else 0

    return {
        "total": total,
        "new": new,
        "contacted": contacted,
        "booked": booked,
        "lost": lost,
        "conversion_rate_percent": conversion_rate
    }