from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime
import os
from app.core.database import SessionLocal
from app.models.user import User
from app.models.patient import Patient
from app.models.appointment import Appointment, AppointmentStatus
from app.auth.auth import get_current_user

router = APIRouter(prefix="/ml", tags=["Machine Learning"])

class PredictionRequest(BaseModel):
    appointment_id: int

class PredictionResponse(BaseModel):
    appointment_id: int
    patient_name: str
    no_show_probability: float
    risk_level: str
    recommendation: str

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def calculate_risk_score(patient, appointment, db):
    \"\"\"Calculate no-show risk score based on patient history\"\"\"
    risk_score = 0.0
    
    # Factor 1: Past missed appointments (40% weight)
    past_appointments = db.query(Appointment).filter(
        Appointment.patient_id == patient.id,
        Appointment.id < appointment.id,
        Appointment.status.in_([AppointmentStatus.COMPLETED, AppointmentStatus.NO_SHOW, AppointmentStatus.CANCELLED])
    ).all()
    
    total_past = len(past_appointments)
    missed_past = sum(1 for a in past_appointments if a.status == AppointmentStatus.NO_SHOW)
    cancelled_past = sum(1 for a in past_appointments if a.status == AppointmentStatus.CANCELLED)
    
    if total_past > 0:
        miss_rate = missed_past / total_past
        risk_score += miss_rate * 40
    
    # Factor 2: Cancellation history (20% weight)
    if total_past > 0:
        cancel_rate = cancelled_past / total_past
        risk_score += cancel_rate * 20
    
    # Factor 3: Appointment time (15% weight)
    apt_hour = appointment.appointment_date.hour
    if apt_hour < 9 or apt_hour > 17:
        risk_score += 10  # Early morning or late evening
    elif 12 <= apt_hour <= 13:
        risk_score += 8   # Lunch time
    
    # Factor 4: Day of week (15% weight)
    apt_day = appointment.appointment_date.weekday()
    if apt_day >= 5:  # Weekend
        risk_score += 10
    elif apt_day == 0 or apt_day == 6:  # Monday or Sunday
        risk_score += 8
    
    # Factor 5: Age factor (10% weight)
    if patient.date_of_birth:
        age = datetime.now().year - patient.date_of_birth.year
        if age < 25:
            risk_score += 5
        elif age > 60:
            risk_score += 8
    
    return min(risk_score, 100)  # Cap at 100

@router.post("/predict-no-show", response_model=PredictionResponse)
def predict_no_show(
    request: PredictionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    \"\"\"Predict probability of patient missing their appointment\"\"\"
    
    # Get appointment
    appointment = db.query(Appointment).filter(Appointment.id == request.appointment_id).first()
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    
    # Get patient
    patient = db.query(Patient).filter(Patient.id == appointment.patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    # Calculate risk score
    probability = calculate_risk_score(patient, appointment, db)
    
    # Determine risk level and recommendation
    if probability < 30:
        risk_level = "Low"
        recommendation = "Standard reminder sufficient"
    elif probability < 60:
        risk_level = "Medium"
        recommendation = "Send extra reminder 2 days before"
    else:
        risk_level = "High"
        recommendation = "Call patient to confirm, offer rescheduling"
    
    return PredictionResponse(
        appointment_id=appointment.id,
        patient_name=f"{patient.first_name} {patient.last_name}",
        no_show_probability=round(probability, 1),
        risk_level=risk_level,
        recommendation=recommendation
    )

@router.get("/model-status")
def get_model_status(current_user: User = Depends(get_current_user)):
    \"\"\"Check if ML model is available\"\"\"
    return {
        "model_loaded": True,
        "model_type": "Rule-based risk scoring",
        "features": ["Past attendance", "Cancellation history", "Appointment time", "Day of week", "Patient age"]
    }
