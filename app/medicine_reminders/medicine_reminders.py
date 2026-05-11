from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from typing import List
from app.core.database import SessionLocal
from app.models.user import User
from app.models.medicine_reminder import MedicineReminder
from app.schemas.medicine_reminder import (
    MedicineReminderCreate,
    MedicineReminderUpdate,
    MedicineReminderResponse
)
from app.auth.auth import get_current_user

router = APIRouter(prefix="/medicine-reminders", tags=["Medicine Reminders"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/", response_model=MedicineReminderResponse, status_code=status.HTTP_201_CREATED)
def create_reminder(
        data: MedicineReminderCreate,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """Schedule a medicine reminder for a patient."""
    reminder = MedicineReminder(**data.model_dump())
    db.add(reminder)
    db.commit()
    db.refresh(reminder)
    return reminder


@router.get("/", response_model=List[MedicineReminderResponse])
def get_all_reminders(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    return db.query(MedicineReminder).order_by(MedicineReminder.created_at.desc()).all()


@router.get("/patient/{patient_id}", response_model=List[MedicineReminderResponse])
def get_patient_reminders(
        patient_id: int,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """Get all medicine reminders for a specific patient."""
    return db.query(MedicineReminder).filter(
        MedicineReminder.patient_id == patient_id
    ).all()


@router.put("/{reminder_id}", response_model=MedicineReminderResponse)
def update_reminder(
        reminder_id: int,
        data: MedicineReminderUpdate,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    reminder = db.query(MedicineReminder).filter(MedicineReminder.id == reminder_id).first()
    if not reminder:
        raise HTTPException(status_code=404, detail="Reminder not found")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(reminder, field, value)
    db.commit()
    db.refresh(reminder)
    return reminder


@router.delete("/{reminder_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_reminder(
        reminder_id: int,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    reminder = db.query(MedicineReminder).filter(MedicineReminder.id == reminder_id).first()
    if not reminder:
        raise HTTPException(status_code=404, detail="Reminder not found")
    db.delete(reminder)
    db.commit()


@router.patch("/{reminder_id}/toggle", response_model=MedicineReminderResponse)
def toggle_reminder(
        reminder_id: int,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """Activate or deactivate a reminder."""
    reminder = db.query(MedicineReminder).filter(MedicineReminder.id == reminder_id).first()
    if not reminder:
        raise HTTPException(status_code=404, detail="Reminder not found")
    reminder.is_active = not reminder.is_active
    db.commit()
    db.refresh(reminder)
    return reminder