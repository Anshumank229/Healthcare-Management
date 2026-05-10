from sqlalchemy import Column, Integer, String, Date, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base

class Patient(Base):
    __tablename__ = "patients"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    date_of_birth = Column(Date, nullable=False)
    phone = Column(String, nullable=False)
    email = Column(String, nullable=False)
    address = Column(Text)
    blood_group = Column(String(5))
    allergies = Column(Text)
    medical_conditions = Column(Text)
    emergency_contact_name = Column(String)
    emergency_contact_phone = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="patient", lazy="select")
    appointments = relationship("Appointment", back_populates="patient", lazy="select", foreign_keys="Appointment.patient_id")
    notifications = relationship("Notification", back_populates="patient", lazy="select")