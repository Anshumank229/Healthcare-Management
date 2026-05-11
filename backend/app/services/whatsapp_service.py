import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class WhatsAppService:
    def __init__(self):
        self.access_token = os.getenv("WHATSAPP_ACCESS_TOKEN")
        self.phone_number_id = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
        self.api_version = os.getenv("WHATSAPP_API_VERSION", "v25.0")
        self.api_url = os.getenv("WHATSAPP_API_URL", "https://graph.facebook.com")

    def send_text_message(self, to_number: str, message: str) -> dict:
        """Send a text message via WhatsApp"""
        url = f"{self.api_url}/{self.api_version}/{self.phone_number_id}/messages"

        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }

        data = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to_number,
            "type": "text",
            "text": {
                "preview_url": False,
                "body": message
            }
        }

        response = requests.post(url, headers=headers, json=data)
        return response.json()

    def send_appointment_reminder(self, to_number: str, patient_name: str,
                                  doctor_name: str, appointment_date: str,
                                  appointment_time: str) -> dict:
        """Send appointment reminder"""
        message = f"""🏥 *Appointment Reminder*

Dear {patient_name},

This is a reminder of your upcoming appointment with *Dr. {doctor_name}*.

📅 *Date:* {appointment_date}
⏰ *Time:* {appointment_time}

Please reply:
• CONFIRM - to confirm your attendance
• RESCHEDULE - to change the time
• CANCEL - to cancel the appointment

Thank you for choosing Healthcare Platform!"""

        return self.send_text_message(to_number, message)

# Create a singleton instance
whatsapp_service = WhatsAppService()