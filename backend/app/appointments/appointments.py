from fastapi import APIRouter, HTTPException, Depends, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from typing import List, Optional
from datetime import datetime, timedelta
from app.core.database import SessionLocal
from app.models.user import User
from app.models.patient import Patient
from app.models.appointment import Appointment, AppointmentStatus
from app.schemas.appointments import (
    AppointmentCreate, AppointmentUpdate,
    AppointmentResponse, AppointmentWithDetails
)
from app.auth.auth import get_current_user

router = APIRouter(prefix="/appointments", tags=["Appointments"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/", response_model=AppointmentResponse, status_code=status.HTTP_201_CREATED)
def create_appointment(
        appointment_data: AppointmentCreate,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """Create a new appointment"""

    # Check if patient exists
    patient = db.query(Patient).filter(Patient.id == appointment_data.patient_id).first()
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found"
        )

    # Check if doctor exists
    doctor = db.query(User).filter(
        and_(User.id == appointment_data.doctor_id, User.role == "doctor")
    ).first()
    if not doctor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Doctor not found"
        )

    # Check for conflicting appointments
    # Step 1: Fetch candidates from DB (only use column comparisons, no timedelta on columns)
    end_time = appointment_data.appointment_date + timedelta(minutes=appointment_data.duration_minutes)

    candidates = db.query(Appointment).filter(
        and_(
            Appointment.doctor_id == appointment_data.doctor_id,
            Appointment.appointment_date < end_time,
            Appointment.status.notin_([AppointmentStatus.CANCELLED, AppointmentStatus.COMPLETED])
        )
    ).all()

    # Step 2: Check overlap in Python where duration_minutes is a real integer
    conflicting = next(
        (apt for apt in candidates
         if apt.appointment_date + timedelta(minutes=apt.duration_minutes) > appointment_data.appointment_date),
        None
    )

    if conflicting:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Doctor already has an appointment at this time"
        )

    # Create appointment
    appointment = Appointment(
        **appointment_data.dict(),
        created_by=current_user.id,
        status=AppointmentStatus.SCHEDULED
    )

    db.add(appointment)
    db.commit()
    db.refresh(appointment)

    return appointment

@router.get("/", response_model=List[AppointmentResponse])
def get_appointments(
        patient_id: Optional[int] = Query(None, description="Filter by patient ID"),
        doctor_id: Optional[int] = Query(None, description="Filter by doctor ID"),
        status: Optional[AppointmentStatus] = Query(None, description="Filter by status"),
        from_date: Optional[datetime] = Query(None, description="From date"),
        to_date: Optional[datetime] = Query(None, description="To date"),
        skip: int = 0,
        limit: int = 100,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """Get appointments with filters"""

    query = db.query(Appointment)

    # Apply filters
    if patient_id:
        query = query.filter(Appointment.patient_id == patient_id)
    if doctor_id:
        query = query.filter(Appointment.doctor_id == doctor_id)
    if status:
        query = query.filter(Appointment.status == status)
    if from_date:
        query = query.filter(Appointment.appointment_date >= from_date)
    if to_date:
        query = query.filter(Appointment.appointment_date <= to_date)

    # Role-based restrictions
    if current_user.role == "patient":
        # Patients can only see their own appointments
        patient = db.query(Patient).filter(Patient.user_id == current_user.id).first()
        if patient:
            query = query.filter(Appointment.patient_id == patient.id)
        else:
            return []
    elif current_user.role == "doctor":
        # Doctors can only see their own appointments
        query = query.filter(Appointment.doctor_id == current_user.id)

    appointments = query.order_by(Appointment.appointment_date).offset(skip).limit(limit).all()
    return appointments

@router.get("/doctor/{doctor_id}/availability")
def get_doctor_availability(
        doctor_id: int,
        date: datetime = Query(..., description="Date to check availability (YYYY-MM-DD)"),
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """Check doctor's available time slots for a given date"""

    # Working hours (9 AM to 5 PM)
    start_hour = 9
    end_hour = 17
    slot_duration = 30  # minutes

    # Get existing appointments for the doctor on this date
    start_of_day = datetime(date.year, date.month, date.day, start_hour, 0, 0)
    end_of_day = datetime(date.year, date.month, date.day, end_hour, 0, 0)

    existing_appointments = db.query(Appointment).filter(
        and_(
            Appointment.doctor_id == doctor_id,
            Appointment.appointment_date >= start_of_day,
            Appointment.appointment_date <= end_of_day,
            Appointment.status.notin_([AppointmentStatus.CANCELLED, AppointmentStatus.COMPLETED])
        )
    ).all()

    # Generate available slots
    available_slots = []
    current_time = start_of_day

    while current_time < end_of_day:
        is_available = True
        for apt in existing_appointments:
            apt_end = apt.appointment_date + timedelta(minutes=apt.duration_minutes)
            if current_time < apt_end and current_time + timedelta(minutes=slot_duration) > apt.appointment_date:
                is_available = False
                break

        if is_available:
            available_slots.append(current_time.strftime("%H:%M"))

        current_time += timedelta(minutes=slot_duration)

    return {
        "doctor_id": doctor_id,
        "date": date.strftime("%Y-%m-%d"),
        "available_slots": available_slots
    }

@router.get("/{appointment_id}", response_model=AppointmentWithDetails)
def get_appointment(
        appointment_id: int,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """Get appointment by ID with patient and doctor details"""

    appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if not appointment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appointment not found"
        )

    # Check permissions
    patient = db.query(Patient).filter(Patient.id == appointment.patient_id).first()
    if current_user.role == "patient" and patient.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    if current_user.role == "doctor" and appointment.doctor_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )

    # Get additional details
    doctor = db.query(User).filter(User.id == appointment.doctor_id).first()
    patient = db.query(Patient).filter(Patient.id == appointment.patient_id).first()

    return {
        **appointment.__dict__,
        "patient_name": f"{patient.first_name} {patient.last_name}",
        "doctor_name": doctor.full_name
    }

@router.put("/{appointment_id}", response_model=AppointmentResponse)
def update_appointment(
        appointment_id: int,
        appointment_data: AppointmentUpdate,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """Update appointment details"""

    appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if not appointment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appointment not found"
        )

    # Check permissions
    patient = db.query(Patient).filter(Patient.id == appointment.patient_id).first()
    if current_user.role == "patient" and patient.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )

    # Update fields
    for field, value in appointment_data.dict(exclude_unset=True).items():
        setattr(appointment, field, value)

    db.commit()
    db.refresh(appointment)

    return appointment

@router.delete("/{appointment_id}", status_code=status.HTTP_204_NO_CONTENT)
def cancel_appointment(
        appointment_id: int,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """Cancel appointment (sets status to cancelled)"""

    appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if not appointment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appointment not found"
        )

    # Check permissions
    patient = db.query(Patient).filter(Patient.id == appointment.patient_id).first()
    if current_user.role not in ["admin", "staff"]:
        if current_user.role == "patient" and patient.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        if current_user.role == "doctor" and appointment.doctor_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )

    appointment.status = AppointmentStatus.CANCELLED
    db.commit()

    return None