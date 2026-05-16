from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime
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
    risk_score = 0.0
    
    past_appointments = db.query(Appointment).filter(
        Appointment.patient_id == patient.id,
        Appointment.id < appointment.id,
        Appointment.status.in_([AppointmentStatus.COMPLETED, AppointmentStatus.NO_SHOW, AppointmentStatus.CANCELLED])
    ).all()
    
    total_past = len(past_appointments)
    missed_past = sum(1 for a in past_appointments if a.status == AppointmentStatus.NO_SHOW)
    
    if total_past > 0:
        miss_rate = missed_past / total_past
        risk_score += miss_rate * 40
    
    return min(risk_score, 100)

@router.post("/predict-no-show", response_model=PredictionResponse)
def predict_no_show(
    request: PredictionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    appointment = db.query(Appointment).filter(Appointment.id == request.appointment_id).first()
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    
    patient = db.query(Patient).filter(Patient.id == appointment.patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    probability = calculate_risk_score(patient, appointment, db)
    
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
    return {"model_loaded": True, "model_type": "Rule-based risk scoring"}
