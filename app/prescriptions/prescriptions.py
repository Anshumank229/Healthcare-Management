import json
from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from typing import List
from app.core.database import SessionLocal
from app.models.user import User
from app.models.prescription import Prescription
from app.schemas.prescription import PrescriptionCreate, PrescriptionUpdate, PrescriptionResponse
from app.auth.auth import get_current_user

router = APIRouter(prefix="/prescriptions", tags=["Prescriptions"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/", response_model=PrescriptionResponse, status_code=status.HTTP_201_CREATED)
def create_prescription(
        data: PrescriptionCreate,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """Doctor creates a prescription for a patient."""
    medicines_json = json.dumps([m.model_dump() for m in data.medicines])
    prescription = Prescription(
        patient_id=data.patient_id,
        doctor_id=current_user.id,
        medicines=medicines_json,
        duration=data.duration,
        notes=data.notes,
        next_visit_date=data.next_visit_date
    )
    db.add(prescription)
    db.commit()
    db.refresh(prescription)
    return prescription


@router.get("/", response_model=List[PrescriptionResponse])
def get_all_prescriptions(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    return db.query(Prescription).order_by(Prescription.created_at.desc()).all()


@router.get("/patient/{patient_id}", response_model=List[PrescriptionResponse])
def get_patient_prescriptions(
        patient_id: int,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """Get all prescriptions for a specific patient."""
    return db.query(Prescription).filter(
        Prescription.patient_id == patient_id
    ).order_by(Prescription.created_at.desc()).all()


@router.get("/{prescription_id}", response_model=PrescriptionResponse)
def get_prescription(
        prescription_id: int,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    prescription = db.query(Prescription).filter(Prescription.id == prescription_id).first()
    if not prescription:
        raise HTTPException(status_code=404, detail="Prescription not found")
    return prescription


@router.put("/{prescription_id}", response_model=PrescriptionResponse)
def update_prescription(
        prescription_id: int,
        data: PrescriptionUpdate,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    prescription = db.query(Prescription).filter(Prescription.id == prescription_id).first()
    if not prescription:
        raise HTTPException(status_code=404, detail="Prescription not found")

    if data.medicines is not None:
        prescription.medicines = json.dumps([m.model_dump() for m in data.medicines])
    if data.duration is not None:
        prescription.duration = data.duration
    if data.notes is not None:
        prescription.notes = data.notes
    if data.next_visit_date is not None:
        prescription.next_visit_date = data.next_visit_date

    db.commit()
    db.refresh(prescription)
    return prescription


@router.delete("/{prescription_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_prescription(
        prescription_id: int,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    prescription = db.query(Prescription).filter(Prescription.id == prescription_id).first()
    if not prescription:
        raise HTTPException(status_code=404, detail="Prescription not found")
    db.delete(prescription)
    db.commit()