from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.core.database import engine, Base
from app.whatsapp import router as whatsapp_router
from app.models import User, Patient, Notification, Lead, Prescription, MedicineReminder
from app.auth import auth
from app.patients import patients
from app.appointments import appointments
from app.notifications import notifications
from app.leads import leads
from app.prescriptions import prescriptions
from app.medicine_reminders import medicine_reminders
from app.ai import chatbot
from app.analytics import analytics
from app.services.scheduler import start_scheduler, stop_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    Base.metadata.create_all(bind=engine)
    start_scheduler()
    yield
    # Shutdown
    stop_scheduler()


app = FastAPI(
    title="Healthcare Platform API",
    description="AI Patient Follow-up Automation Platform",
    version="2.0.0",
    lifespan=lifespan
)


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
app.include_router(whatsapp_router)
app.include_router(leads.router)
app.include_router(prescriptions.router)
app.include_router(medicine_reminders.router)
app.include_router(chatbot.router)
app.include_router(analytics.router)