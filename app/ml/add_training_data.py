from app.core.database import SessionLocal
from app.models.appointment import Appointment, AppointmentStatus
from app.models.patient import Patient
from datetime import datetime, timedelta
import random

def add_training_data():
    db = SessionLocal()

    # Get existing patients
    patients = db.query(Patient).all()
    if not patients:
        print("❌ No patients found. Create patients first.")
        return

    # Create sample appointments with attended/no-show status
    appointments_data = []

    for i in range(5000):  # Create 50 training examples
        patient = random.choice(patients)

        # Random date in last 3 months
        days_ago = random.randint(1, 90)
        apt_date = datetime.now() - timedelta(days=days_ago)

        # Random status: 70% completed, 30% no-show
        is_no_show = random.random() < 0.3
        status = AppointmentStatus.NO_SHOW if is_no_show else AppointmentStatus.COMPLETED

        appointment = Appointment(
            patient_id=patient.id,
            doctor_id=2,  # Assuming doctor ID 2 exists
            appointment_date=apt_date,
            duration_minutes=30,
            reason="Training data",
            status=status,
            attended=not is_no_show,
            created_by=1
        )
        appointments_data.append(appointment)

    # Add to database
    db.add_all(appointments_data)
    db.commit()

    print(f"✅ Added {len(appointments_data)} training appointments")
    print(f"   Completed: {sum(1 for a in appointments_data if a.status == AppointmentStatus.COMPLETED)}")
    print(f"   No-shows: {sum(1 for a in appointments_data if a.status == AppointmentStatus.NO_SHOW)}")

    db.close()

if __name__ == "__main__":
    add_training_data()