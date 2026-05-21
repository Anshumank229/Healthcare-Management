import os
import requests
import logging
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

class WhatsAppService:
    def __init__(self):
        self.access_token = os.getenv('WHATSAPP_ACCESS_TOKEN')
        self.phone_number_id = os.getenv('WHATSAPP_PHONE_NUMBER_ID')
        self.api_version = os.getenv('WHATSAPP_API_VERSION', 'v25.0')
        self.api_url = os.getenv('WHATSAPP_API_URL', 'https://graph.facebook.com')

    def send_text_message(self, to_number: str, message: str) -> dict:
        url = f'{self.api_url}/{self.api_version}/{self.phone_number_id}/messages'
        headers = {'Authorization': f'Bearer {self.access_token}', 'Content-Type': 'application/json'}
        data = {'messaging_product': 'whatsapp', 'recipient_type': 'individual', 'to': to_number, 'type': 'text', 'text': {'preview_url': False, 'body': message}}
        response = requests.post(url, headers=headers, json=data)
        return response.json()

    def send_text_message_with_retry(self, to_number: str, message: str) -> dict:
        """Send message with Redis-backed retry queue on failure"""
        try:
            result = self.send_text_message(to_number, message)
            if "error" in result:
                # Add to Redis retry queue
                from app.core.redis_client import redis_client
                redis_client.add_to_retry_queue({
                    "to_number": to_number,
                    "message": message,
                    "original_error": result.get("error")
                })
                logger.warning(f"Message queued for retry to {to_number}")
            return result
        except Exception as e:
            from app.core.redis_client import redis_client
            redis_client.add_to_retry_queue({
                "to_number": to_number,
                "message": message,
                "error": str(e)
            })
            logger.error(f"Message queued for retry due to: {e}")
            return {"error": str(e), "queued": True}

    def send_appointment_reminder(self, to_number: str, patient_name: str, doctor_name: str, appointment_date: str, appointment_time: str) -> dict:
        message = f'''🏥 *Appointment Reminder*

Dear {patient_name},

This is a reminder of your upcoming appointment with *Dr. {doctor_name}*.

📅 *Date:* {appointment_date}
⏰ *Time:* {appointment_time}

Please reply:
• CONFIRM - to confirm your attendance
• RESCHEDULE - to change the time
• CANCEL - to cancel the appointment

Thank you for choosing Healthcare Platform!'''
        return self.send_text_message_with_retry(to_number, message)

    def send_doctor_notification(self, to_number: str, doctor_name: str, patient_name: str, appointment_date: str, appointment_time: str) -> dict:
        message = f'''👨‍⚕️ *New Appointment Booked*

Dear Dr. {doctor_name},

A new appointment has been booked with *{patient_name}*.

📅 *Date:* {appointment_date}
⏰ *Time:* {appointment_time}

Please ensure you are available at the scheduled time.

Thank you,
Healthcare Platform'''
        return self.send_text_message_with_retry(to_number, message)

    def send_daily_checkin(self, to_number: str, patient_name: str) -> dict:
        message = f'''🌞 *Daily Health Check-in*

Good morning, {patient_name}!

How are you feeling today?

Reply with:
• 👍 - Feeling good
• 😐 - Feeling okay
• 👎 - Need assistance

Healthcare Platform cares about your health!'''
        return self.send_text_message_with_retry(to_number, message)

    def send_followup_reminder(self, to_number: str, patient_name: str, appointment_date: str, days_remaining: int) -> dict:
        message = f'''👋 *Follow-up Reminder*

Dear {patient_name},

This is a reminder that your follow-up appointment is in *{days_remaining} days*.

📅 *Date:* {appointment_date}

Please reply CONFIRM to confirm or call the clinic to reschedule.

Thank you,
Healthcare Platform'''
        return self.send_text_message_with_retry(to_number, message)

    def send_missed_appointment_notice(self, to_number: str, patient_name: str, appointment_date: str) -> dict:
        message = f'''⚠️ *Missed Appointment Notice*

Dear {patient_name},

You missed your appointment scheduled on {appointment_date}.

Please call the clinic to reschedule as soon as possible.

Thank you,
Healthcare Platform'''
        return self.send_text_message_with_retry(to_number, message)

whatsapp_service = WhatsAppService()