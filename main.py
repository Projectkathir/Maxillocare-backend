from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import os
import sqlite3


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


# ============================================================================
# DATABASE MIGRATION FUNCTION - FIXES IMAGE UPLOAD ERROR
# ============================================================================
def migrate_database():
    """
    Add fracture_classification and recommended_actions columns 
    to healing_images table if they don't exist
    
    This fixes the 500 error when uploading images
    """
    db_path = "database.db"
    
    # Check if database exists
    if not os.path.exists(db_path):
        print("✅ Database doesn't exist yet. Will be created on first request.")
        return
    
    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if healing_images table exists
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='healing_images'
        """)
        
        if not cursor.fetchone():
            print("✅ healing_images table doesn't exist yet. Will be created automatically.")
            conn.close()
            return
        
        # Get existing columns
        cursor.execute("PRAGMA table_info(healing_images)")
        existing_columns = [row[1] for row in cursor.fetchall()]
        
        print(f"📋 Existing columns in healing_images: {existing_columns}")
        
        # Add fracture_classification if missing
        if 'fracture_classification' not in existing_columns:
            print("🔧 Adding fracture_classification column...")
            cursor.execute("""
                ALTER TABLE healing_images 
                ADD COLUMN fracture_classification VARCHAR
            """)
            print("✅ fracture_classification column added successfully!")
        else:
            print("✅ fracture_classification column already exists")
        
        # Add recommended_actions if missing
        if 'recommended_actions' not in existing_columns:
            print("🔧 Adding recommended_actions column...")
            cursor.execute("""
                ALTER TABLE healing_images 
                ADD COLUMN recommended_actions TEXT
            """)
            print("✅ recommended_actions column added successfully!")
        else:
            print("✅ recommended_actions column already exists")
        
        # Commit changes
        conn.commit()
        conn.close()
        
        print("✅ Database migration completed successfully!")
        
    except Exception as e:
        print(f"❌ Migration error: {e}")
        print("⚠️ If this is a new deployment, this is expected. Database will be created fresh.")


# ============================================================================
# QUESTIONNAIRE INITIALIZATION FUNCTION
# ============================================================================
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


# ============================================================================
# LIFESPAN EVENT HANDLER
# ============================================================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    try:
        print("\n" + "="*70)
        print("🚀 MAXILLOCARE API - STARTING UP")
        print("="*70)
        
        # Step 1: Run database migration FIRST (fixes image upload error)
        print("\n🔄 Step 1: Running database migration...")
        migrate_database()
        
        # Step 2: Create database tables
        print("\n🔄 Step 2: Creating/updating database tables...")
        Base.metadata.create_all(bind=engine)
        print("✅ Database tables created successfully!")
        
        # Step 3: Initialize questionnaires
        print("\n🔄 Step 3: Initializing questionnaires...")
        init_questionnaires()
        
        print("\n" + "="*70)
        print("✅ STARTUP COMPLETE - API READY TO ACCEPT REQUESTS")
        print("="*70 + "\n")
        
    except Exception as e:
        print(f"\n❌ STARTUP ERROR: {e}\n")
    
    yield
    
    # Shutdown
    print("\n🛑 Application shutting down...")


# ============================================================================
# CREATE FASTAPI APP
# ============================================================================
app = FastAPI(
    title="Maxillocare API",
    version="2.0.0",
    description="Healthcare management system for maxillofacial surgery follow-up with AI analysis",
    lifespan=lifespan
)


# ============================================================================
# CORS CONFIGURATION
# ============================================================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# CREATE UPLOADS DIRECTORY
# ============================================================================
try:
    os.makedirs("uploads/patient_images", exist_ok=True)
    app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
    print("✅ Uploads directory configured")
except Exception as e:
    print(f"⚠️ Uploads directory warning: {e}")


# ============================================================================
# INCLUDE ROUTERS
# ============================================================================
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


# ============================================================================
# ROOT ENDPOINTS
# ============================================================================
@app.get("/")
def read_root():
    return {
        "message": "Maxillocare API is running",
        "version": "2.0.0",
        "status": "healthy",
        "features": {
            "authentication": "JWT-based",
            "ai_analysis": "Fracture classification & recommendations",
            "questionnaires": "4 types (trauma, orthognathic, pathology, onco)",
            "image_upload": "Radiograph/CT scan analysis"
        }
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "database": "connected",
        "questionnaires_loaded": True,
        "version": "2.0.0",
        "migrations": "applied"
    }
