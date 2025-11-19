"""
AI Analysis Router - Gemini-Powered Medical Image Analysis
Supports dental X-rays, CT scans, and clinical images
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from database import get_db
from models.user import User
from models.image import HealingImage
from models.patient import Patient
from schemas.image_schema import AIAnalysisResult, HealingImage as HealingImageSchema
from utils.security import get_current_user

# Import Gemini service
try:
    from services.gemini_service import gemini_service
    GEMINI_AVAILABLE = gemini_service is not None
except ImportError:
    GEMINI_AVAILABLE = False
    print("⚠️ WARNING: Gemini service not available. Check GEMINI_API_KEY.")

router = APIRouter()


@router.post("/analyze/{image_id}", response_model=AIAnalysisResult, status_code=status.HTTP_200_OK)
def analyze_image(
    image_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Analyze medical image with AI-powered diagnostics
    
    **Supported Image Types:**
    - Panoramic X-rays (OPG)
    - CT scans and CBCT
    - Intraoral radiographs
    - Clinical photographs
    - Post-operative healing images
    
    **Returns:**
    - Fracture classification (if applicable)
    - Clinical observations and findings
    - Evidence-based treatment recommendations
    """
    
    # Check if Gemini service is available
    if not GEMINI_AVAILABLE:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI analysis service unavailable. Please contact administrator."
        )
    
    # Fetch image record
    image = db.query(HealingImage).filter(HealingImage.id == image_id).first()
    if not image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image not found"
        )
    
    # Verify patient exists
    patient = db.query(Patient).filter(Patient.id == image.patient_id).first()
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found"
        )
    
    # Authorization check - patients can only analyze their own images
    if current_user.role == "patient":
        patient_user = db.query(Patient).filter(Patient.user_id == current_user.id).first()
        if not patient_user or patient_user.id != image.patient_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to analyze this image"
            )
    
    # Prevent re-analysis (to save Gemini API quota on free tier)
    if image.analyzed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Image already analyzed. Use GET /results/{image_id} to retrieve existing analysis."
        )
    
    try:
        # Perform Gemini AI analysis
        print(f"🔍 Starting AI analysis for image ID: {image_id}")
        analysis_result = gemini_service.analyze_dental_image(image.image_path)
        
        # Update image record with AI results (still store healing_percentage in DB)
        image.healing_percentage = analysis_result['healing_percentage']
        image.ai_remarks = analysis_result['ai_remarks']
        image.fracture_classification = analysis_result['fracture_classification']
        image.recommended_actions = analysis_result['recommended_actions']
        image.analyzed = True
        
        # Update patient's current healing percentage (internal tracking)
        patient.current_healing_percentage = analysis_result['healing_percentage']
        
        # Commit to database
        db.commit()
        db.refresh(image)
        
        print(f"✅ Analysis completed - Healing: {image.healing_percentage}%")
        
        # Return analysis results (WITHOUT healing_percentage in response)
        return AIAnalysisResult(
            image_id=image.id,
            # healing_percentage=image.healing_percentage,  ← REMOVED
            ai_remarks=image.ai_remarks,
            fracture_classification=image.fracture_classification,
            recommended_actions=image.recommended_actions,
            analyzed_at=datetime.utcnow()
        )
        
    except FileNotFoundError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Image file not found: {str(e)}"
        )
    
    except Exception as e:
        db.rollback()
        print(f"❌ AI analysis error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI analysis failed: {str(e)}"
        )


@router.get("/results/{image_id}", response_model=AIAnalysisResult)
def get_analysis_results(
    image_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieve AI analysis results for a specific image
    
    **Returns:** Complete analysis including classification and recommendations
    """
    
    image = db.query(HealingImage).filter(HealingImage.id == image_id).first()
    
    if not image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image not found"
        )
    
    if not image.analyzed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Image has not been analyzed yet. Use POST /analyze/{image_id} first."
        )
    
    # Authorization check
    if current_user.role == "patient":
        patient = db.query(Patient).filter(Patient.user_id == current_user.id).first()
        if not patient or patient.id != image.patient_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view this analysis"
            )
    
    # Return analysis results (WITHOUT healing_percentage in response)
    return AIAnalysisResult(
        image_id=image.id,
        # healing_percentage=image.healing_percentage,  ← REMOVED
        ai_remarks=image.ai_remarks,
        fracture_classification=image.fracture_classification,
        recommended_actions=image.recommended_actions,
        analyzed_at=image.upload_date
    )


@router.get("/history/{patient_id}", response_model=List[HealingImageSchema])
def get_patient_analysis_history(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get chronological healing progress for a patient
    
    **Returns:** All analyzed images with AI results, sorted by upload date
    """
    
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found"
        )
    
    # Authorization check
    if current_user.role == "patient":
        patient_user = db.query(Patient).filter(Patient.user_id == current_user.id).first()
        if not patient_user or patient_user.id != patient_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view this patient's history"
            )
    
    # Fetch all analyzed images
    analyzed_images = db.query(HealingImage).filter(
        HealingImage.patient_id == patient_id,
        HealingImage.analyzed == True
    ).order_by(HealingImage.upload_date.asc()).all()
    
    return analyzed_images
