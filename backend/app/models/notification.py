from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum

class NotificationType(str, enum.Enum):
    APPOINTMENT_REMINDER = "appointment_reminder"
    MEDICINE_REMINDER = "medicine_reminder"
    FOLLOW_UP_REMINDER = "follow_up_reminder"
    PAYMENT_REMINDER = "payment_reminder"

class NotificationStatus(str, enum.Enum):
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    CANCELLED = "cancelled"

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    appointment_id = Column(Integer, ForeignKey("appointments.id"), nullable=True)
    message_type = Column(Enum(NotificationType), nullable=False)
    message_content = Column(String, nullable=False)
    recipient_phone = Column(String, nullable=False)
    status = Column(Enum(NotificationStatus), default=NotificationStatus.PENDING)
    scheduled_time = Column(DateTime, nullable=False)
    sent_time = Column(DateTime, nullable=True)
    whatsapp_message_id = Column(String, nullable=True)
    error_message = Column(String, nullable=True)
    retry_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    patient = relationship("Patient", back_populates="notifications")
    appointment = relationship("Appointment", back_populates="notifications")