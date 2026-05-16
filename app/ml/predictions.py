from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime
import pickle
import os
import pandas as pd

from app.core.database import SessionLocal
from app.models.user import User
from app.models.patient import Patient
from app.models.appointment import Appointment, AppointmentStatus
from app.auth.auth import get_current_user

router = APIRouter(prefix="/ml", tags=["Machine Learning"])

# Model paths
MODEL_PATH = os.path.join(os.path.dirname(__file__), 'models', 'no_show_model.pkl')
ENCODER_PATH = os.path.join(os.path.dirname(__file__), 'models', 'age_label_encoder.pkl')

model = None
age_encoder = None

def load_models():
    global model, age_encoder
    try:
        if os.path.exists(MODEL_PATH):
            with open(MODEL_PATH, 'rb') as f:
                model = pickle.load(f)
        if os.path.exists(ENCODER_PATH):
            with open(ENCODER_PATH, 'rb') as f:
                age_encoder = pickle.load(f)
        return model is not None
    except Exception as e:
        print(f"Error loading models: {e}")
        return False

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

@router.post("/predict-no-show", response_model=PredictionResponse)
def predict_no_show(
        request: PredictionRequest,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """Predict probability of patient missing their appointment"""

    if not load_models():
        raise HTTPException(status_code=503, detail="Model not loaded. Run training first.")

    # Get appointment
    appointment = db.query(Appointment).filter(Appointment.id == request.appointment_id).first()
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")

    # Get patient
    patient = db.query(Patient).filter(Patient.id == appointment.patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    # Get patient history
    past_appointments = db.query(Appointment).filter(
        Appointment.patient_id == patient.id,
        Appointment.id < appointment.id,
        Appointment.status.in_([AppointmentStatus.COMPLETED, AppointmentStatus.NO_SHOW])
    ).all()

    total_past = len(past_appointments)
    missed_past = sum(1 for a in past_appointments if a.status == AppointmentStatus.NO_SHOW)

    # Age group
    age_group = "unknown"
    if patient.date_of_birth:
        age = datetime.now().year - patient.date_of_birth.year
        if age < 35:
            age_group = "18-35"
        elif age <= 50:
            age_group = "35-50"
        else:
            age_group = "50+"

    # Time features
    apt_hour = appointment.appointment_date.hour
    apt_day = appointment.appointment_date.weekday()
    is_weekend = 1 if apt_day >= 5 else 0
    is_morning = 1 if apt_hour < 12 else 0

    # Create feature vector
    age_encoded = 0
    if age_encoder and age_group in age_encoder.classes_:
        age_encoded = age_encoder.transform([age_group])[0]

    features = pd.DataFrame([{
        'age_group': age_encoded,
        'has_phone': 1 if patient.phone else 0,
        'total_past': total_past,
        'missed_past': missed_past,
        'miss_rate': missed_past / total_past if total_past > 0 else 0,
        'apt_hour': apt_hour,
        'apt_day': apt_day,
        'is_weekend': is_weekend,
        'is_morning': is_morning
    }])

    # Predict
    probability = model.predict_proba(features)[0][1] * 100

    # Determine risk level
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
    """Check if model is trained and ready"""
    return {
        "model_loaded": os.path.exists(MODEL_PATH),
        "model_path": MODEL_PATH if os.path.exists(MODEL_PATH) else None
    }