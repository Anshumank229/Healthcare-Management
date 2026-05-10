from app.core.database import engine, Base
from app.models.user import User
from app.models.patient import Patient
from app.models.appointment import Appointment

print("Creating database tables...")
Base.metadata.create_all(bind=engine)
print("✅ Tables created successfully!")