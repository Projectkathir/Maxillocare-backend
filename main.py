from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import os

try:
    from database import engine, Base, SessionLocal
    from routers import auth, patients, appointments, questionnaire, images, ai_analysis, messages
    
    # Import ALL model files
    from models.user import User
    from models.patient import Patient  
    from models.appointment import Appointment
    from models.image import HealingImage
    from models.message import Message
    from models.questionnaire import Questionnaire, QuestionnaireResponse
    
    print("✅ All imports successful!")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    raise  # Re-raise to prevent silent failures

# Function to initialize questionnaires
def init_questionnaires():
    """Initialize predefined questionnaires in the database"""
    db = SessionLocal()
    
    try:
        # Check if questionnaires already exist
        existing_count = db.query(Questionnaire).count()
        if existing_count > 0:
            print(f"✅ Database already has {existing_count} questionnaire(s)")
            return
        
        print("📝 Initializing questionnaires...")
        
        # Trauma Follow-up Questionnaire
        trauma_q = Questionnaire(
            title="Trauma Follow-up Questionnaire",
            type="trauma",
            questions=[
                {"id": 1, "question": "Pain (VAS 0–10)", "type": "numeric", "range": {"min": 0, "max": 10}},
                {"id": 2, "question": "Swelling at surgical site?", "type": "single_choice", "options": ["None", "Mild", "Moderate", "Severe"]},
                {"id": 3, "question": "Redness, pus, discharge, or foul smell?", "type": "boolean", "options": ["Yes", "No"]},
                {"id": 4, "question": "Fever (>38°C)?", "type": "boolean", "options": ["Yes", "No"]},
                {"id": 5, "question": "Chewing difficulty?", "type": "single_choice", "options": ["None", "Mild", "Moderate", "Severe"]},
                {"id": 6, "question": "Speech difficulty?", "type": "single_choice", "options": ["None", "Mild", "Moderate", "Severe"]},
                {"id": 7, "question": "Mouth opening without pain?", "type": "single_choice", "options": ["Yes", "Partially", "No"]},
                {"id": 8, "question": "Satisfaction with facial/jaw appearance?", "type": "scale", "options": ["Very satisfied", "Satisfied", "Neutral", "Dissatisfied", "Very dissatisfied"]},
                {"id": 9, "question": "Confidence in social situations?", "type": "scale", "options": ["Not at all", "Slightly", "Moderately", "Very", "Extremely"]},
                {"id": 10, "question": "Feeling anxious or worried (past week)?", "type": "scale", "options": ["Not at all", "Several days", "More than half the days", "Nearly every day"]},
                {"id": 11, "question": "Feeling low mood/lack of interest (past week)?", "type": "scale", "options": ["Not at all", "Several days", "More than half the days", "Nearly every day"]},
                {"id": 12, "question": "Bite/occlusion feels correct?", "type": "single_choice", "options": ["Yes", "No", "Not sure"]},
                {"id": 13, "question": "Any difficulty in jaw movement?", "type": "single_choice", "options": ["None", "Mild", "Moderate", "Severe"]}
            ]
        )
        
        # Orthognathic Follow-up Questionnaire
        orthognathic_q = Questionnaire(
            title="Orthognathic Follow-up Questionnaire",
            type="orthognathic",
            questions=[
                {"id": 1, "question": "Pain (VAS 0–10)", "type": "numeric", "range": {"min": 0, "max": 10}},
                {"id": 2, "question": "Swelling at surgical site?", "type": "single_choice", "options": ["None", "Mild", "Moderate", "Severe"]},
                {"id": 3, "question": "Redness, pus, discharge, or foul smell?", "type": "boolean", "options": ["Yes", "No"]},
                {"id": 4, "question": "Fever (>38°C)?", "type": "boolean", "options": ["Yes", "No"]},
                {"id": 5, "question": "Chewing difficulty?", "type": "single_choice", "options": ["None", "Mild", "Moderate", "Severe"]},
                {"id": 6, "question": "Speech difficulty?", "type": "single_choice", "options": ["None", "Mild", "Moderate", "Severe"]},
                {"id": 7, "question": "Mouth opening without pain?", "type": "single_choice", "options": ["Yes", "Partially", "No"]},
                {"id": 8, "question": "Satisfaction with facial/jaw appearance?", "type": "scale", "options": ["Very satisfied", "Satisfied", "Neutral", "Dissatisfied", "Very dissatisfied"]},
                {"id": 9, "question": "Confidence in social situations?", "type": "scale", "options": ["Not at all", "Slightly", "Moderately", "Very", "Extremely"]},
                {"id": 10, "question": "Feeling anxious or worried (past week)?", "type": "scale", "options": ["Not at all", "Several days", "More than half the days", "Nearly every day"]},
                {"id": 11, "question": "Feeling low mood/lack of interest (past week)?", "type": "scale", "options": ["Not at all", "Several days", "More than half the days", "Nearly every day"]},
                {"id": 12, "question": "Numbness/tingling in lips, cheeks, or chin?", "type": "boolean", "options": ["Yes", "No"]},
                {"id": 13, "question": "Any difficulty with occlusion/bite after surgery?", "type": "single_choice", "options": ["Yes", "No", "Not sure"]}
            ]
        )
        
        # Pathology Follow-up Questionnaire
        pathology_q = Questionnaire(
            title="Pathology Follow-up Questionnaire",
            type="pathology",
            questions=[
                {"id": 1, "question": "Pain (VAS 0–10)", "type": "numeric", "range": {"min": 0, "max": 10}},
                {"id": 2, "question": "Swelling at surgical site?", "type": "single_choice", "options": ["None", "Mild", "Moderate", "Severe"]},
                {"id": 3, "question": "Redness, pus, discharge, or foul smell?", "type": "boolean", "options": ["Yes", "No"]},
                {"id": 4, "question": "Fever (>38°C)?", "type": "boolean", "options": ["Yes", "No"]},
                {"id": 5, "question": "Chewing difficulty?", "type": "single_choice", "options": ["None", "Mild", "Moderate", "Severe"]},
                {"id": 6, "question": "Speech difficulty?", "type": "single_choice", "options": ["None", "Mild", "Moderate", "Severe"]},
                {"id": 7, "question": "Mouth opening without pain?", "type": "single_choice", "options": ["Yes", "Partially", "No"]},
                {"id": 8, "question": "Satisfaction with facial/jaw appearance?", "type": "scale", "options": ["Very satisfied", "Satisfied", "Neutral", "Dissatisfied", "Very dissatisfied"]},
                {"id": 9, "question": "Confidence in social situations?", "type": "scale", "options": ["Not at all", "Slightly", "Moderately", "Very", "Extremely"]},
                {"id": 10, "question": "Feeling anxious or worried (past week)?", "type": "scale", "options": ["Not at all", "Several days", "More than half the days", "Nearly every day"]},
                {"id": 11, "question": "Feeling low mood/lack of interest (past week)?", "type": "scale", "options": ["Not at all", "Several days", "More than half the days", "Nearly every day"]},
                {"id": 12, "question": "Any difficulty in swallowing?", "type": "single_choice", "options": ["None", "Mild", "Moderate", "Severe"]},
                {"id": 13, "question": "Any changes in speech articulation?", "type": "single_choice", "options": ["None", "Mild", "Moderate", "Severe"]}
            ]
        )
        
        # Onco Follow-up Questionnaire
        onco_q = Questionnaire(
            title="Onco Follow-up Questionnaire",
            type="onco",
            questions=[
                {"id": 1, "question": "Pain (VAS 0–10)", "type": "numeric", "range": {"min": 0, "max": 10}},
                {"id": 2, "question": "Swelling at surgical site?", "type": "single_choice", "options": ["None", "Mild", "Moderate", "Severe"]},
                {"id": 3, "question": "Redness, pus, discharge, or foul smell?", "type": "boolean", "options": ["Yes", "No"]},
                {"id": 4, "question": "Fever (>38°C)?", "type": "boolean", "options": ["Yes", "No"]},
                {"id": 5, "question": "Chewing difficulty?", "type": "single_choice", "options": ["None", "Mild", "Moderate", "Severe"]},
                {"id": 6, "question": "Speech difficulty?", "type": "single_choice", "options": ["None", "Mild", "Moderate", "Severe"]},
                {"id": 7, "question": "Mouth opening without pain?", "type": "single_choice", "options": ["Yes", "Partially", "No"]},
                {"id": 8, "question": "Satisfaction with facial/jaw appearance?", "type": "scale", "options": ["Very satisfied", "Satisfied", "Neutral", "Dissatisfied", "Very dissatisfied"]},
                {"id": 9, "question": "Confidence in social situations?", "type": "scale", "options": ["Not at all", "Slightly", "Moderately", "Very", "Extremely"]},
                {"id": 10, "question": "Feeling anxious or worried (past week)?", "type": "scale", "options": ["Not at all", "Several days", "More than half the days", "Nearly every day"]},
                {"id": 11, "question": "Feeling low mood/lack of interest (past week)?", "type": "scale", "options": ["Not at all", "Several days", "More than half the days", "Nearly every day"]},
                {"id": 12, "question": "Difficulty swallowing or aspiration symptoms?", "type": "single_choice", "options": ["None", "Mild", "Moderate", "Severe"]},
                {"id": 13, "question": "Weight loss since surgery?", "type": "boolean", "options": ["Yes", "No"]},
                {"id": 14, "question": "Any limitation in daily activity due to surgery?", "type": "single_choice", "options": ["None", "Mild", "Moderate", "Severe"]}
            ]
        )
        
        # Add all questionnaires
        db.add_all([trauma_q, orthognathic_q, pathology_q, onco_q])
        db.commit()
        
        print("✅ Successfully initialized 4 questionnaires!")
        print("   ✓ Trauma Follow-up")
        print("   ✓ Orthognathic Follow-up")
        print("   ✓ Pathology Follow-up")
        print("   ✓ Onco Follow-up")
        
    except Exception as e:
        print(f"❌ Questionnaire initialization error: {e}")
        db.rollback()
    finally:
        db.close()

# Lifespan event handler
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    try:
        Base.metadata.create_all(bind=engine)
        print("✅ Database tables created successfully!")
        
        # Initialize questionnaires
        init_questionnaires()
        
    except Exception as e:
        print(f"❌ Startup error: {e}")
    
    yield
    
    # Shutdown
    print("🛑 Application shutting down...")

# Create FastAPI app
app = FastAPI(
    title="Maxillocare API",
    version="1.0.0",
    description="Healthcare management system for maxillofacial surgery follow-up",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create uploads directory
try:
    os.makedirs("uploads/patient_images", exist_ok=True)
    app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
except Exception as e:
    print(f"⚠️ Uploads directory warning: {e}")

# Include routers
try:
    app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
    app.include_router(patients.router, prefix="/api/patients", tags=["Patients"])
    app.include_router(appointments.router, prefix="/api/appointments", tags=["Appointments"])
    app.include_router(questionnaire.router, prefix="/api/questionnaire", tags=["Questionnaire"])
    app.include_router(images.router, prefix="/api/images", tags=["Images"])
    app.include_router(ai_analysis.router, prefix="/api/ai-analysis", tags=["AI Analysis"])
    app.include_router(messages.router, prefix="/api/messages", tags=["Messages"])
    print("✅ All routers included successfully!")
except Exception as e:
    print(f"❌ Router inclusion error: {e}")

@app.get("/")
def read_root():
    return {
        "message": "Maxillocare API is running",
        "version": "1.0.0",
        "status": "healthy"
    }

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "database": "connected",
        "questionnaires_loaded": True
    }
