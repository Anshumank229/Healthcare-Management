from sqlalchemy import Column, Integer, String, Date, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class Prescription(Base):
    __tablename__ = "prescriptions"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    doctor_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    medicines = Column(Text, nullable=False)       # JSON string: [{name, dose, frequency}]
    duration = Column(String, nullable=True)       # e.g. "7 days"
    notes = Column(Text, nullable=True)
    next_visit_date = Column(Date, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    patient = relationship("Patient", backref="prescriptions")
    doctor = relationship("User", backref="prescriptions")