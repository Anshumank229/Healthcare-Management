import requests
from app.services.whatsapp_service import whatsapp_service
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
from app.services.whatsapp_service import whatsapp_service

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
    """Create a new appointment - automatically sends WhatsApp reminder"""

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
    end_time = appointment_data.appointment_date + timedelta(minutes=appointment_data.duration_minutes)

    candidates = db.query(Appointment).filter(
        and_(
            Appointment.doctor_id == appointment_data.doctor_id,
            Appointment.appointment_date < end_time,
            Appointment.status.notin_([AppointmentStatus.CANCELLED, AppointmentStatus.COMPLETED])
        )
    ).all()

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

    # ✅ SEND WHATSAPP REMINDER ✅
    try:
        formatted_date = appointment.appointment_date.strftime("%B %d, %Y")
        formatted_time = appointment.appointment_date.strftime("%I:%M %p")

        whatsapp_service.send_appointment_reminder(
            to_number=patient.phone,
            patient_name=f"{patient.first_name} {patient.last_name}",
            doctor_name=doctor.full_name.replace("Dr.", "").strip(),
            appointment_date=formatted_date,
            appointment_time=formatted_time
        )
        print(f"✅ WhatsApp reminder sent to {patient.phone}")
    except Exception as e:
        print(f"⚠️ WhatsApp error (appointment still created): {e}")

    # ✅ TRIGGER n8n WORKFLOW for scheduled reminder (24 hours before)
    try:
        n8n_webhook = "http://localhost:5678/webhook/appointment-reminder"

        payload = {
            "patient_name": f"{patient.first_name} {patient.last_name}",
            "phone": patient.phone,
            "doctor_name": doctor.full_name.replace("Dr.", "").strip(),
            "appointment_date": formatted_date,
            "appointment_time": formatted_time,
            "appointment_id": appointment.id,
            "reason": appointment.reason
        }

        # Send to n8n asynchronously (don't wait for response)
        import threading
        def trigger_n8n():
            try:
                requests.post(n8n_webhook, json=payload, timeout=5)
                print(f"✅ n8n workflow triggered for appointment {appointment.id}")
            except Exception as e:
                print(f"⚠️ n8n trigger failed: {e}")

        threading.Thread(target=trigger_n8n).start()

    except Exception as e:
        print(f"⚠️ n8n trigger setup error: {e}")

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
        patient = db.query(Patient).filter(Patient.user_id == current_user.id).first()
        if patient:
            query = query.filter(Appointment.patient_id == patient.id)
        else:
            return []
    elif current_user.role == "doctor":
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

    start_hour = 9
    end_hour = 17
    slot_duration = 30

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

    patient = db.query(Patient).filter(Patient.id == appointment.patient_id).first()
    if current_user.role == "patient" and patient.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )

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