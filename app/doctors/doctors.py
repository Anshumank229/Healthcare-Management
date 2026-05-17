from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List, Optional
from app.core.database import SessionLocal
from app.models.user import User
from app.schemas.user import UserResponse
from app.auth.auth import get_current_user

router = APIRouter(prefix="/doctors", tags=["Doctors"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/", response_model=List[UserResponse])
def get_doctors(
        search: Optional[str] = Query(None, description="Search by name, specialty, or degree"),
        specialty: Optional[str] = Query(None, description="Filter by specialty"),
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """Get all doctors with search and filter options"""
    query = db.query(User).filter(User.role == "doctor")

    if search:
        query = query.filter(
            or_(
                User.full_name.ilike(f"%{search}%"),
                User.specialty.ilike(f"%{search}%"),
                User.degree.ilike(f"%{search}%")
            )
        )

    if specialty:
        query = query.filter(User.specialty == specialty)

    return query.all()

@router.get("/specialties")
def get_specialties(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """Get all unique doctor specialties"""
    specialties = db.query(User.specialty).filter(User.role == "doctor", User.specialty.isnot(None)).distinct().all()
    return [s[0] for s in specialties if s[0]]

@router.get("/{doctor_id}", response_model=UserResponse)
def get_doctor(
        doctor_id: int,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """Get doctor by ID"""
    doctor = db.query(User).filter(User.id == doctor_id, User.role == "doctor").first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")
    return doctor