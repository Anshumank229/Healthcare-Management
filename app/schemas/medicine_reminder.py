from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class MedicineReminderCreate(BaseModel):
    patient_id: int
    prescription_id: int
    medicine_name: str
    dose: str
    frequency: str
    reminder_time: str   # "HH:MM" format e.g. "09:00"
    phone: str           # patient WhatsApp number e.g. "919876543210"


class MedicineReminderUpdate(BaseModel):
    reminder_time: Optional[str] = None
    is_active: Optional[bool] = None
    dose: Optional[str] = None
    frequency: Optional[str] = None


class MedicineReminderResponse(BaseModel):
    id: int
    patient_id: int
    prescription_id: int
    medicine_name: str
    dose: str
    frequency: str
    reminder_time: str
    phone: str
    is_active: bool
    last_sent_at: Optional[datetime] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True