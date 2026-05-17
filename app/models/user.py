from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    role = Column(String, default="patient", nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Doctor-specific fields
    specialty = Column(String, nullable=True)  # e.g., "Cardiologist", "Dermatologist"
    degree = Column(String, nullable=True)    # e.g., "MD", "MBBS", "DM"
    experience_years = Column(Integer, default=0)
    consultation_fee = Column(Integer, default=500)
    bio = Column(Text, nullable=True)
    profile_image = Column(String, nullable=True)

    # Relationships
    patient = relationship("Patient", back_populates="user", uselist=False, lazy="select")
    doctor_appointments = relationship("Appointment", foreign_keys="Appointment.doctor_id", back_populates="doctor", lazy="select")
    created_appointments = relationship("Appointment", foreign_keys="Appointment.created_by", back_populates="creator", lazy="select")