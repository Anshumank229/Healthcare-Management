from fastapi import FastAPI
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from slowapi.middleware import SlowAPIMiddleware
from app.services.followup_service import start_followup_scheduler, stop_followup_scheduler
from app.core.database import engine, Base
from app.core.rate_limit import setup_rate_limiting
from app.whatsapp import router as whatsapp_router
from app.models import User, Patient, Notification, Lead, Prescription, MedicineReminder
from app.auth import auth
from app.patients import patients
from app.appointments import appointments
from app.notifications import notifications
from app.leads import leads
from app.prescriptions import prescriptions
from app.medicine_reminders import medicine_reminders
from app.analytics import analytics
from app.services.scheduler import start_scheduler, stop_scheduler
from app.ml import predictions
from app.doctors import doctors  # Add this import


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    Base.metadata.create_all(bind=engine)
    start_scheduler()
    start_followup_scheduler()  # ✅ Start followup scheduler here
    yield
    # Shutdown
    stop_scheduler()
    stop_followup_scheduler()   # ✅ Stop followup scheduler here


app = FastAPI(
    title="Healthcare Platform API",
    description="AI Patient Follow-up Automation Platform",
    version="2.0.0",
    lifespan=lifespan
)


# CORS must be first — before any other middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://healthcare-dashboard-gamma-nine.vercel.app",
        "https://healthcare-dashboard-uyha.onrender.com",
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:5174",
    ],
    allow_origin_regex=r"https://.*\.(vercel\.app|onrender\.com)",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate limiting after CORS
setup_rate_limiting(app)
app.add_middleware(SlowAPIMiddleware)


@app.get("/")
def root():
    return {"message": "Healthcare API is running", "status": "healthy"}

@app.get("/health")
def health_check():
    return {"status": "ok", "database": "connected"}


# Include routers
app.include_router(auth.router)
app.include_router(patients.router)
app.include_router(appointments.router)
app.include_router(notifications.router)
app.include_router(whatsapp_router)
app.include_router(leads.router)
app.include_router(prescriptions.router)
app.include_router(medicine_reminders.router)
app.include_router(predictions.router)
app.include_router(analytics.router)
app.include_router(doctors.router)  # ✅ Add doctors router