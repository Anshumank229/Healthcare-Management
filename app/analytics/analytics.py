from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, case
from datetime import date, timedelta, datetime
from app.core.database import SessionLocal
from app.models.user import User
from app.models.patient import Patient
from app.models.appointment import Appointment
from app.models.lead import Lead, LeadStatus
from app.models.prescription import Prescription
from app.auth.auth import get_current_user

router = APIRouter(prefix="/analytics", tags=["Analytics"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ─────────────────────────────────────────────
# 1. OVERVIEW DASHBOARD
# ─────────────────────────────────────────────
@router.get("/overview")
def overview(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """Top-level numbers for the admin dashboard."""
    today = date.today()
    thirty_days_ago = today - timedelta(days=30)

    total_patients = db.query(Patient).count()
    total_appointments = db.query(Appointment).count()
    total_leads = db.query(Lead).count()
    converted_leads = db.query(Lead).filter(Lead.status == LeadStatus.booked).count()

    appointments_today = db.query(Appointment).filter(
        func.date(Appointment.appointment_date) == today
    ).count()

    new_patients_this_month = db.query(Patient).filter(
        func.date(Patient.created_at) >= thirty_days_ago
    ).count() if hasattr(Patient, "created_at") else 0

    new_leads_this_month = db.query(Lead).filter(
        func.date(Lead.created_at) >= thirty_days_ago
    ).count()

    conversion_rate = round((converted_leads / total_leads * 100), 1) if total_leads > 0 else 0

    return {
        "total_patients": total_patients,
        "total_appointments": total_appointments,
        "total_leads": total_leads,
        "converted_leads": converted_leads,
        "lead_conversion_rate_percent": conversion_rate,
        "appointments_today": appointments_today,
        "new_patients_this_month": new_patients_this_month,
        "new_leads_this_month": new_leads_this_month,
    }


# ─────────────────────────────────────────────
# 2. APPOINTMENT ANALYTICS
# ─────────────────────────────────────────────
@router.get("/appointments")
def appointment_analytics(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """Breakdown of appointments by status."""
    total = db.query(Appointment).count()

    # Count by status — adjust status values to match your model
    status_counts = db.query(
        Appointment.status,
        func.count(Appointment.id).label("count")
    ).group_by(Appointment.status).all()

    status_breakdown = {row.status: row.count for row in status_counts}

    # No-show rate
    no_show = status_breakdown.get("no_show", 0) or status_breakdown.get("no-show", 0)
    no_show_rate = round((no_show / total * 100), 1) if total > 0 else 0

    # Completed
    completed = status_breakdown.get("completed", 0)
    completion_rate = round((completed / total * 100), 1) if total > 0 else 0

    # Appointments in last 7 days
    seven_days_ago = date.today() - timedelta(days=7)
    last_week = db.query(Appointment).filter(
        func.date(Appointment.appointment_date) >= seven_days_ago
    ).count()

    # Upcoming appointments
    upcoming = db.query(Appointment).filter(
        func.date(Appointment.appointment_date) >= date.today()
    ).count()

    return {
        "total_appointments": total,
        "status_breakdown": status_breakdown,
        "no_show_count": no_show,
        "no_show_rate_percent": no_show_rate,
        "completed_count": completed,
        "completion_rate_percent": completion_rate,
        "appointments_last_7_days": last_week,
        "upcoming_appointments": upcoming,
    }


# ─────────────────────────────────────────────
# 3. LEAD ANALYTICS
# ─────────────────────────────────────────────
@router.get("/leads")
def lead_analytics(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """Lead funnel and source breakdown."""
    total = db.query(Lead).count()

    # By status
    status_counts = db.query(
        Lead.status,
        func.count(Lead.id).label("count")
    ).group_by(Lead.status).all()
    status_breakdown = {row.status: row.count for row in status_counts}

    # By source
    source_counts = db.query(
        Lead.source,
        func.count(Lead.id).label("count")
    ).group_by(Lead.source).all()
    source_breakdown = {str(row.source): row.count for row in source_counts}

    # Best performing source
    best_source = max(source_breakdown, key=source_breakdown.get) if source_breakdown else None

    booked = status_breakdown.get("booked", 0)
    lost = status_breakdown.get("lost", 0)
    conversion_rate = round((booked / total * 100), 1) if total > 0 else 0

    return {
        "total_leads": total,
        "status_breakdown": status_breakdown,
        "source_breakdown": source_breakdown,
        "best_performing_source": best_source,
        "converted": booked,
        "lost": lost,
        "conversion_rate_percent": conversion_rate,
    }


# ─────────────────────────────────────────────
# 4. FOLLOW-UP ANALYTICS
# ─────────────────────────────────────────────
@router.get("/followups")
def followup_analytics(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """Patients due for follow-up visits."""
    today = date.today()
    next_7_days = today + timedelta(days=7)
    overdue_date = today - timedelta(days=1)

    # Due in next 7 days
    due_soon = db.query(Prescription).filter(
        Prescription.next_visit_date >= today,
        Prescription.next_visit_date <= next_7_days
    ).count()

    # Overdue (next_visit_date already passed)
    overdue = db.query(Prescription).filter(
        Prescription.next_visit_date < today
    ).count()

    # Patients with prescriptions (have follow-up scheduled)
    with_followup = db.query(Prescription).filter(
        Prescription.next_visit_date.isnot(None)
    ).count()

    # Upcoming follow-ups with patient details
    upcoming_details = db.query(Prescription, Patient).join(
        Patient, Prescription.patient_id == Patient.id
    ).filter(
        Prescription.next_visit_date >= today,
        Prescription.next_visit_date <= next_7_days
    ).all()

    upcoming_list = [
        {
            "patient_name": patient.full_name,
            "patient_phone": patient.phone,
            "next_visit_date": str(prescription.next_visit_date),
            "prescription_id": prescription.id,
        }
        for prescription, patient in upcoming_details
    ]

    return {
        "followups_due_in_7_days": due_soon,
        "overdue_followups": overdue,
        "total_patients_with_followup_scheduled": with_followup,
        "upcoming_followup_details": upcoming_list,
    }


# ─────────────────────────────────────────────
# 5. PATIENT RETENTION
# ─────────────────────────────────────────────
@router.get("/retention")
def retention_analytics(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """How many patients returned for a second visit."""
    total_patients = db.query(Patient).count()

    # Patients with more than 1 appointment = repeat patients
    repeat_patients = db.query(Appointment.patient_id).group_by(
        Appointment.patient_id
    ).having(func.count(Appointment.id) > 1).count()

    single_visit = total_patients - repeat_patients
    retention_rate = round((repeat_patients / total_patients * 100), 1) if total_patients > 0 else 0

    # New patients in last 30 days
    thirty_days_ago = date.today() - timedelta(days=30)
    new_this_month = db.query(Appointment.patient_id).filter(
        func.date(Appointment.appointment_date) >= thirty_days_ago
    ).distinct().count()

    return {
        "total_patients": total_patients,
        "repeat_patients": repeat_patients,
        "single_visit_patients": single_visit,
        "retention_rate_percent": retention_rate,
        "active_patients_last_30_days": new_this_month,
    }


# ─────────────────────────────────────────────
# 6. DOCTOR PERFORMANCE
# ─────────────────────────────────────────────
@router.get("/doctors")
def doctor_analytics(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """Appointments per doctor."""
    doctor_stats = db.query(
        Appointment.doctor_id,
        User.full_name,
        func.count(Appointment.id).label("total_appointments")
    ).join(User, Appointment.doctor_id == User.id).group_by(
        Appointment.doctor_id, User.full_name
    ).all()

    return {
        "doctor_performance": [
            {
                "doctor_id": row.doctor_id,
                "doctor_name": row.full_name,
                "total_appointments": row.total_appointments,
            }
            for row in doctor_stats
        ]
    }