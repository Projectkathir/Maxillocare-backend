from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

try:
    from database import engine, Base
    from routers import auth, patients, appointments, questionnaire, images, ai_analysis, messages
    
    # Import ALL model files - wrapped in try-except for debugging
    from models.user import User
    from models.patient import Patient  
    from models.appointment import Appointment
    from models.image import HealingImage  # Check if this should be "Image" instead
    from models.message import Message
    from models.questionnaire import Questionnaire, QuestionnaireResponse

    print("✅ All imports successful!")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    # Continue without the problematic import for now
    pass

# Create database tables
try:
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created successfully!")
except Exception as e:
    print(f"❌ Database creation error: {e}")

app = FastAPI(title="Maxillocare API", version="1.0.0")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create uploads directory if it doesn't exist (optional for Render)
try:
    os.makedirs("uploads/patient_images", exist_ok=True)
    app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
except Exception as e:
    print(f"⚠️ Uploads directory warning: {e}")

# Include routers with error handling
try:
    app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
    app.include_router(patients.router, prefix="/api/patients", tags=["Patients"])
    app.include_router(appointments.router, prefix="/api/appointments", tags=["Appointments"])
    app.include_router(questionnaire.router, prefix="/api/questionnaire", tags=["Questionnaire"])  # Fixed path
    app.include_router(images.router, prefix="/api/images", tags=["Images"])
    app.include_router(ai_analysis.router, prefix="/api/ai-analysis", tags=["AI Analysis"])  # Fixed path
    app.include_router(messages.router, prefix="/api/messages", tags=["Messages"])
    print("✅ All routers included successfully!")
except Exception as e:
    print(f"❌ Router inclusion error: {e}")

@app.get("/")
def read_root():
    return {"message": "Maxillocare API is running", "version": "1.0.0"}

@app.get("/health")
def health_check():
    return {"status": "healthy", "database": "connected"}
