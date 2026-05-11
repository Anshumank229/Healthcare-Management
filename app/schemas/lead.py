from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from app.models.lead import LeadSource, LeadStatus


class LeadCreate(BaseModel):
    name: str
    phone: str
    age: Optional[int] = None
    problem: Optional[str] = None
    preferred_date: Optional[str] = None
    source: Optional[LeadSource] = LeadSource.other
    campaign: Optional[str] = None
    notes: Optional[str] = None


class LeadUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    age: Optional[int] = None
    problem: Optional[str] = None
    preferred_date: Optional[str] = None
    source: Optional[LeadSource] = None
    campaign: Optional[str] = None
    status: Optional[LeadStatus] = None
    notes: Optional[str] = None


class LeadResponse(BaseModel):
    id: int
    name: str
    phone: str
    age: Optional[int] = None
    problem: Optional[str] = None
    preferred_date: Optional[str] = None
    source: Optional[LeadSource] = None
    campaign: Optional[str] = None
    status: LeadStatus
    notes: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True