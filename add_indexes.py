from app.core.database import engine
from sqlalchemy import text

def add_indexes():
    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_appointments_doctor_id ON appointments(doctor_id);",
        "CREATE INDEX IF NOT EXISTS idx_appointments_patient_id ON appointments(patient_id);",
        "CREATE INDEX IF NOT EXISTS idx_appointments_appointment_date ON appointments(appointment_date);",
        "CREATE INDEX IF NOT EXISTS idx_appointments_status ON appointments(status);",
        "CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);",
        "CREATE INDEX IF NOT EXISTS idx_patients_phone ON patients(phone);",
    ]
    
    print("Adding database indexes...")
    with engine.connect() as conn:
        for idx in indexes:
            try:
                conn.execute(text(idx))
                print(f"✅ {idx[:50]}...")
            except Exception as e:
                print(f"❌ Error: {e}")
        conn.commit()
    
    print("✅ All indexes created successfully!")

if __name__ == "__main__":
    add_indexes()
