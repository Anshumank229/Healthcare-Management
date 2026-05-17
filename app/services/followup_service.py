from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta
from app.core.database import SessionLocal
from app.models.appointment import Appointment, AppointmentStatus
from app.models.patient import Patient
from app.services.whatsapp_service import whatsapp_service
import logging

logger = logging.getLogger(__name__)
scheduler = BackgroundScheduler()

def send_daily_checkins():
    db = SessionLocal()
    try:
        today = datetime.now().date()
        today_start = datetime.combine(today, datetime.min.time())
        today_end = datetime.combine(today, datetime.max.time())
        
        appointments = db.query(Appointment).filter(
            Appointment.appointment_date >= today_start,
            Appointment.appointment_date <= today_end,
            Appointment.status == AppointmentStatus.CONFIRMED
        ).all()
        
        for apt in appointments:
            patient = db.query(Patient).filter(Patient.id == apt.patient_id).first()
            if patient and patient.phone:
                whatsapp_service.send_daily_checkin(patient.phone, f"{patient.first_name} {patient.last_name}")
                logger.info(f'Daily check-in sent to {patient.phone}')
    except Exception as e:
        logger.error(f'Daily check-in error: {e}')
    finally:
        db.close()

def check_missed_appointments():
    db = SessionLocal()
    try:
        yesterday = datetime.now() - timedelta(days=1)
        yesterday_start = datetime.combine(yesterday.date(), datetime.min.time())
        yesterday_end = datetime.combine(yesterday.date(), datetime.max.time())
        
        missed = db.query(Appointment).filter(
            Appointment.appointment_date >= yesterday_start,
            Appointment.appointment_date <= yesterday_end,
            Appointment.status == AppointmentStatus.SCHEDULED
        ).all()
        
        for apt in missed:
            apt.status = AppointmentStatus.NO_SHOW
            patient = db.query(Patient).filter(Patient.id == apt.patient_id).first()
            if patient and patient.phone:
                formatted_date = apt.appointment_date.strftime('%B %d, %Y')
                whatsapp_service.send_missed_appointment_notice(
                    patient.phone,
                    f'{patient.first_name} {patient.last_name}',
                    formatted_date
                )
                logger.info(f'Missed notice sent to {patient.phone}')
        db.commit()
    except Exception as e:
        logger.error(f'Missed appointment error: {e}')
    finally:
        db.close()

def send_followup_reminders():
    db = SessionLocal()
    try:
        reminder_date = datetime.now() + timedelta(days=2)
        reminder_start = datetime.combine(reminder_date.date(), datetime.min.time())
        reminder_end = datetime.combine(reminder_date.date(), datetime.max.time())
        
        upcoming = db.query(Appointment).filter(
            Appointment.appointment_date >= reminder_start,
            Appointment.appointment_date <= reminder_end,
            Appointment.status == AppointmentStatus.CONFIRMED
        ).all()
        
        for apt in upcoming:
            patient = db.query(Patient).filter(Patient.id == apt.patient_id).first()
            if patient and patient.phone:
                formatted_date = apt.appointment_date.strftime('%B %d, %Y')
                whatsapp_service.send_followup_reminder(
                    patient.phone,
                    f'{patient.first_name} {patient.last_name}',
                    formatted_date,
                    2
                )
                logger.info(f'Follow-up reminder sent to {patient.phone}')
    except Exception as e:
        logger.error(f'Follow-up reminder error: {e}')
    finally:
        db.close()

def start_followup_scheduler():
    if not scheduler.running:
        scheduler.add_job(send_daily_checkins, 'cron', hour=9, minute=0, id='daily_checkins')
        scheduler.add_job(check_missed_appointments, 'cron', hour=0, minute=5, id='missed_check')
        scheduler.add_job(send_followup_reminders, 'cron', hour=10, minute=0, id='followup_reminders')
        scheduler.start()
        logger.info('✅ Follow-up scheduler started')

def stop_followup_scheduler():
    if scheduler.running:
        scheduler.shutdown()
        logger.info('🛑 Follow-up scheduler stopped')
