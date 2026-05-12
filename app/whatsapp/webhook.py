from fastapi import APIRouter, Request, HTTPException, Query
from fastapi.responses import PlainTextResponse, JSONResponse
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.patient import Patient
from app.models.appointment import Appointment, AppointmentStatus
from app.services.whatsapp_service import whatsapp_service

import json
import logging

router = APIRouter(prefix="/whatsapp", tags=["WhatsApp"])
logger = logging.getLogger(__name__)

VERIFY_TOKEN = "healthcare_webhook_2024"

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/webhook")
async def verify_webhook(
        hub_mode: str = Query(None, alias="hub.mode"),
        hub_token: str = Query(None, alias="hub.verify_token"),
        hub_challenge: int = Query(None, alias="hub.challenge")
):
    """WhatsApp webhook verification endpoint"""
    if hub_mode == "subscribe" and hub_token == VERIFY_TOKEN:
        logger.info("✅ Webhook verified successfully!")
        return PlainTextResponse(str(hub_challenge))

    raise HTTPException(status_code=403, detail="Verification failed")


@router.post("/webhook")
async def handle_webhook(request: Request):
    """Handle incoming WhatsApp messages from patients"""
    db = next(get_db())

    try:
        body = await request.json()
        logger.info(f"📨 Webhook received")

        # Process each entry
        for entry in body.get("entry", []):
            for change in entry.get("changes", []):
                value = change.get("value", {})

                # Check for incoming messages
                messages = value.get("messages", [])
                for message in messages:
                    # Get sender's phone number
                    from_number = message.get("from")

                    # Get message text
                    text_obj = message.get("text", {})
                    message_text = text_obj.get("body", "").strip().upper()

                    logger.info(f"📱 Message from {from_number}: {message_text}")

                    # Process the reply
                    await process_patient_reply(db, from_number, message_text)

        return JSONResponse(content={"status": "ok"})

    except Exception as e:
        logger.error(f"❌ Webhook error: {e}")
        return JSONResponse(content={"status": "error"}, status_code=500)
    finally:
        db.close()


async def process_patient_reply(db: Session, phone_number: str, reply: str):
    """Process patient's reply and update appointment status"""
    try:
        # Find patient by phone number
        patient = db.query(Patient).filter(Patient.phone == phone_number).first()

        if not patient:
            logger.warning(f"❌ No patient found with phone: {phone_number}")
            return

        # Find upcoming appointments (not cancelled/completed)
        appointment = db.query(Appointment).filter(
            Appointment.patient_id == patient.id,
            Appointment.status.in_([AppointmentStatus.SCHEDULED, AppointmentStatus.CONFIRMED])
        ).order_by(Appointment.appointment_date).first()

        if not appointment:
            logger.warning(f"❌ No upcoming appointment for patient: {patient.id}")
            # Send message that no appointment found
            whatsapp_service.send_text_message(
                phone_number,
                "📋 You don't have any upcoming appointments. Please book one via our website or call the clinic."
            )
            return

        # Process reply
        if reply == "CONFIRM":
            appointment.status = AppointmentStatus.CONFIRMED
            db.commit()
            logger.info(f"✅ Appointment {appointment.id} confirmed by patient")

            # Send confirmation message
            formatted_date = appointment.appointment_date.strftime("%B %d, %Y")
            formatted_time = appointment.appointment_date.strftime("%I:%M %p")

            confirmation_msg = f"""✅ *Appointment Confirmed!*

Your appointment has been confirmed.

📅 *Date:* {formatted_date}
⏰ *Time:* {formatted_time}
👨‍⚕️ *Doctor:* Dr. {appointment.doctor.full_name.replace('Dr.', '').strip()}

Please arrive 10 minutes early.
Thank you for choosing Healthcare Platform!"""

            whatsapp_service.send_text_message(phone_number, confirmation_msg)

        elif reply == "CANCEL":
            appointment.status = AppointmentStatus.CANCELLED
            db.commit()
            logger.info(f"❌ Appointment {appointment.id} cancelled by patient")

            # Send cancellation confirmation
            cancel_msg = f"""❌ *Appointment Cancelled*

Your appointment on {appointment.appointment_date.strftime('%B %d, %Y')} at {appointment.appointment_date.strftime('%I:%M %p')} has been cancelled.

Please call the clinic to reschedule if needed."""

            whatsapp_service.send_text_message(phone_number, cancel_msg)

        elif reply == "RESCHEDULE":
            # Send message to call clinic
            reschedule_msg = """📞 *Reschedule Request*

Please call our clinic at [YOUR_CLINIC_NUMBER] to reschedule your appointment.

Our staff will help you find a better time slot.

Thank you!"""

            whatsapp_service.send_text_message(phone_number, reschedule_msg)

        else:
            # Unknown reply - send help message
            help_msg = """🤔 *I didn't understand that.*

Please reply with one of these options:
• CONFIRM - to confirm your appointment
• CANCEL - to cancel your appointment
• RESCHEDULE - to change the time

Thank you!"""

            whatsapp_service.send_text_message(phone_number, help_msg)

    except Exception as e:
        logger.error(f"❌ Error processing reply: {e}")