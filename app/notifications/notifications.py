from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.core.database import SessionLocal
from app.models.user import User
from app.models.notification import Notification
from app.auth.auth import get_current_user

router = APIRouter(prefix="/notifications", tags=["Notifications"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/")
def get_notifications(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """Get all notifications"""
    notifications = db.query(Notification).all()
    return [
        {
            "id": n.id,
            "patient_id": n.patient_id,
            "message_type": n.message_type,
            "message_content": n.message_content,
            "status": n.status,
            "scheduled_time": n.scheduled_time,
            "created_at": n.created_at
        }
        for n in notifications
    ]