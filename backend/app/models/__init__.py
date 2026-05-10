# Import Base first
from app.core.database import Base

# Import models in dependency order
from app.models.user import User
from app.models.patient import Patient
from app.models.notification import Notification
from app.models.appointment import Appointment

# Export all
__all__ = ["Base", "User", "Patient", "Appointment", "Notification"]



