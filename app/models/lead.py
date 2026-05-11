from sqlalchemy import Column, Integer, String, DateTime, Enum
from sqlalchemy.sql import func
from app.core.database import Base
import enum


class LeadSource(str, enum.Enum):
    facebook = "facebook"
    google = "google"
    website = "website"
    whatsapp = "whatsapp"
    call = "call"
    other = "other"


class LeadStatus(str, enum.Enum):
    new = "new"
    contacted = "contacted"
    booked = "booked"
    lost = "lost"


class Lead(Base):
    __tablename__ = "leads"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    phone = Column(String, nullable=False)
    age = Column(Integer, nullable=True)
    problem = Column(String, nullable=True)
    preferred_date = Column(String, nullable=True)
    source = Column(Enum(LeadSource), default=LeadSource.other)
    campaign = Column(String, nullable=True)
    status = Column(Enum(LeadStatus), default=LeadStatus.new)
    notes = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())