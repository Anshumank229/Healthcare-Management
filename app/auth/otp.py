from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from app.core.redis_client import redis_client
import random

router = APIRouter(prefix="/auth/otp", tags=["Authentication"])

class OTPRequest(BaseModel):
    phone: str

class OTPVerify(BaseModel):
    phone: str
    otp: str

@router.post("/send")
def send_otp(request: OTPRequest):
    """Send OTP to phone number"""
    otp = str(random.randint(100000, 999999))
    redis_client.store_otp(request.phone, otp)
    # In production, send via SMS/WhatsApp
    print(f"OTP for {request.phone}: {otp}")
    return {"message": "OTP sent successfully"}

@router.post("/verify")
def verify_otp(request: OTPVerify):
    """Verify OTP"""
    if redis_client.verify_otp(request.phone, request.otp):
        return {"verified": True}
    raise HTTPException(status_code=400, detail="Invalid OTP")