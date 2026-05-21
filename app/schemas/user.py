from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class UserBase(BaseModel):
    email: EmailStr
    full_name: str
    role: str

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    # Doctor-specific fields
    specialty: Optional[str] = None
    degree: Optional[str] = None
    experience_years: Optional[int] = 0
    consultation_fee: Optional[int] = 500
    bio: Optional[str] = None
    profile_image: Optional[str] = None
    
    class Config:
        from_attributes = True

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None
    specialty: Optional[str] = None
    degree: Optional[str] = None
    experience_years: Optional[int] = None
    consultation_fee: Optional[int] = None
    bio: Optional[str] = None
    profile_image: Optional[str] = None
