from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Time
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class MedicineReminder(Base):
    __tablename__ = "medicine_reminders"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    prescription_id = Column(Integer, ForeignKey("prescriptions.id"), nullable=False)
    medicine_name = Column(String, nullable=False)
    dose = Column(String, nullable=False)           # e.g. "500mg"
    frequency = Column(String, nullable=False)      # e.g. "twice a day"
    reminder_time = Column(String, nullable=False)  # e.g. "09:00", "21:00"
    phone = Column(String, nullable=False)          # WhatsApp number to send to
    is_active = Column(Boolean, default=True)
    last_sent_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    patient = relationship("Patient", backref="medicine_reminders")
    prescription = relationship("Prescription", backref="medicine_reminders")