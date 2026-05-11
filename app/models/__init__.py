# Import Base first
from app.core.database import Base

# Import models in dependency order
from app.models.user import User
from app.models.patient import Patient
from app.models.notification import Notification
from app.models.appointment import Appointment
from app.models.lead import Lead
from app.models.prescription import Prescription
from app.models.medicine_reminder import MedicineReminder

# Export all
__all__ = ["Base", "User", "Patient", "Appointment", "Notification", "Lead", "Prescription", "MedicineReminder"]