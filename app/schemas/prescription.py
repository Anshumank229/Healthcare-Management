from pydantic import BaseModel
from typing import Optional, List
from datetime import date, datetime


class MedicineItem(BaseModel):
    name: str
    dose: str           # e.g. "500mg"
    frequency: str      # e.g. "twice a day"
    timing: Optional[str] = None  # e.g. "after meal"


class PrescriptionCreate(BaseModel):
    patient_id: int
    medicines: List[MedicineItem]
    duration: Optional[str] = None
    notes: Optional[str] = None
    next_visit_date: Optional[date] = None


class PrescriptionUpdate(BaseModel):
    medicines: Optional[List[MedicineItem]] = None
    duration: Optional[str] = None
    notes: Optional[str] = None
    next_visit_date: Optional[date] = None


class PrescriptionResponse(BaseModel):
    id: int
    patient_id: int
    doctor_id: int
    medicines: str        # stored as JSON string in DB
    duration: Optional[str] = None
    notes: Optional[str] = None
    next_visit_date: Optional[date] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True