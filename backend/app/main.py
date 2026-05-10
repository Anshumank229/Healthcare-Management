from fastapi import FastAPI
from app.core.database import engine, Base


from app.models import User, Patient, Notification

from app.auth import auth
from app.patients import patients
from app.appointments import appointments
from app.notifications import notifications

app = FastAPI(
    title="Healthcare Platform API",
    description="Patient retention system with WhatsApp automation",
    version="1.0.0"
)

# ✅ Optional but recommended: create tables on startup
Base.metadata.create_all(bind=engine)

@app.get("/")
def root():
    return {"message": "Healthcare API is running", "status": "healthy"}

@app.get("/health")
def health_check():
    return {"status": "ok", "database": "connected"}

app.include_router(auth.router)
app.include_router(patients.router)
app.include_router(appointments.router)
app.include_router(notifications.router)