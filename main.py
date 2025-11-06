from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from database import engine, Base
from routers import auth, patients, appointments, questionnaire, images, ai_analysis, messages
# Import ALL model files explicitly
from models.user import User
from models.patient import Patient  
from models.appointment import Appointment
from models.image import HealingImage
from models.message import Message
from models.questionnaire import Questionnaire, QuestionnaireResponse

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Maxillocare API", version="1.0.0")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your Android app
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create uploads directory if it doesn't exist
os.makedirs("uploads/patient_images", exist_ok=True)

# Mount static files for image serving
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(patients.router, prefix="/api/patients", tags=["Patients"])
app.include_router(appointments.router, prefix="/api/appointments", tags=["Appointments"])
app.include_router(questionnaire.router, prefix="/api/questionnaires", tags=["Questionnaires"])
app.include_router(images.router, prefix="/api/images", tags=["Images"])
app.include_router(ai_analysis.router, prefix="/api/ai", tags=["AI Analysis"])
app.include_router(messages.router, prefix="/api/messages", tags=["Messages"])

@app.get("/")
def read_root():
    return {"message": "Maxillocare API is running", "version": "1.0.0"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}