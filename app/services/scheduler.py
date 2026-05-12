from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from app.core.database import SessionLocal
from app.models.medicine_reminder import MedicineReminder
from app.services.whatsapp_service import whatsapp_service  # ✅ CHANGE THIS
import logging

logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()


def send_medicine_reminders():
    """Called every minute by scheduler. Checks if any reminder matches current HH:MM."""
    db: Session = SessionLocal()
    try:
        now = datetime.now()
        current_time = now.strftime("%H:%M")

        reminders = db.query(MedicineReminder).filter(
            MedicineReminder.is_active == True,
            MedicineReminder.reminder_time == current_time
        ).all()

        for reminder in reminders:
            message = (
                f"💊 *Medicine Reminder*\n\n"
                f"Hello! Time to take your medicine.\n\n"
                f"*Medicine:* {reminder.medicine_name}\n"
                f"*Dose:* {reminder.dose}\n"
                f"*Frequency:* {reminder.frequency}\n\n"
                f"Stay healthy! 🌿"
            )
            try:
                # ✅ USE CLASS METHOD INSTEAD
                result = whatsapp_service.send_text_message(reminder.phone, message)
                reminder.last_sent_at = datetime.now(timezone.utc)
                db.commit()
                logger.info(f"Reminder sent to {reminder.phone} for {reminder.medicine_name}")
            except Exception as e:
                logger.error(f"Failed to send reminder {reminder.id}: {e}")

    except Exception as e:
        logger.error(f"Scheduler error: {e}")
    finally:
        db.close()


def send_followup_reminders():
    """Runs daily. Checks prescriptions where next_visit_date is in 2 days."""
    from app.models.prescription import Prescription
    from app.models.patient import Patient
    from datetime import date, timedelta

    db: Session = SessionLocal()
    try:
        target_date = date.today() + timedelta(days=2)

        prescriptions = db.query(Prescription).filter(
            Prescription.next_visit_date == target_date
        ).all()

        for prescription in prescriptions:
            patient = db.query(Patient).filter(
                Patient.id == prescription.patient_id
            ).first()

            if patient and patient.phone:
                message = (
                    f"👋 *Follow-up Reminder*\n\n"
                    f"Hi {patient.full_name}! Your follow-up visit is in 2 days "
                    f"on *{target_date.strftime('%d %b %Y')}*.\n\n"
                    f"Please book your appointment or contact the clinic.\n"
                    f"Stay healthy! 🏥"
                )
                try:
                    # ✅ USE CLASS METHOD INSTEAD
                    whatsapp_service.send_text_message(patient.phone, message)
                    logger.info(f"Follow-up reminder sent to {patient.phone}")
                except Exception as e:
                    logger.error(f"Failed to send follow-up for patient {patient.id}: {e}")

    except Exception as e:
        logger.error(f"Follow-up scheduler error: {e}")
    finally:
        db.close()


def start_scheduler():
    """Start background scheduler. Call this on app startup."""
    if not scheduler.running:
        # Check medicine reminders every minute
        scheduler.add_job(
            send_medicine_reminders,
            CronTrigger(minute="*"),
            id="medicine_reminders",
            replace_existing=True
        )
        # Check follow-up reminders every day at 10 AM
        scheduler.add_job(
            send_followup_reminders,
            CronTrigger(hour=10, minute=0),
            id="followup_reminders",
            replace_existing=True
        )
        scheduler.start()
        logger.info("✅ Scheduler started.")


def stop_scheduler():
    """Stop scheduler on app shutdown."""
    if scheduler.running:
        scheduler.shutdown()
        logger.info("🛑 Scheduler stopped.")