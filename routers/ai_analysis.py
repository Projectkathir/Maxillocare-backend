from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import random
from datetime import datetime

from database import get_db
from models.user import User
from models.image import HealingImage
from models.patient import Patient
from schemas.image_schema import AIAnalysisResult, HealingImage as HealingImageSchema
from utils.security import get_current_user

router = APIRouter()

def mock_ai_analysis(image_path: str) -> dict:
    """
    Mock AI analysis function
    In production, this would call an actual AI model service
    """
    # Generate random healing percentage between 60-95%
    healing_percentage = round(random.uniform(60.0, 95.0), 1)
    
    # Generate remarks based on percentage
    if healing_percentage >= 85:
        remarks = "Excellent healing progress. Tissue regeneration is optimal. No signs of infection or complications."
    elif healing_percentage >= 75:
        remarks = "Good healing progress. Slight inflammation detected but within normal range. Continue current treatment."
    elif healing_percentage >= 65:
        remarks = "Moderate healing progress. Some swelling observed. Monitor closely and follow post-op instructions."
    else:
        remarks = "Healing slower than expected. Possible inflammation or infection. Recommend immediate consultation."
    
    return {
        "healing_percentage": healing_percentage,
        "ai_remarks": remarks
    }

@router.post("/analyze/{image_id}", response_model=AIAnalysisResult)
def analyze_image(
    image_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Get image record
    image = db.query(HealingImage).filter(HealingImage.id == image_id).first()
    
    if not image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image not found"
        )
    
    # Verify access
    patient = db.query(Patient).filter(Patient.id == image.patient_id).first()
    if current_user.role == "patient" and patient.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to analyze this image"
        )
    
    # Perform AI analysis (mock)
    analysis_result = mock_ai_analysis(image.image_path)
    
    # Update image record with analysis results
    image.healing_percentage = analysis_result["healing_percentage"]
    image.ai_remarks = analysis_result["ai_remarks"]
    image.analyzed = True
    
    # Update patient's current healing percentage
    patient.current_healing_percentage = analysis_result["healing_percentage"]
    
    db.commit()
    db.refresh(image)
    
    return AIAnalysisResult(
        image_id=image.id,
        healing_percentage=image.healing_percentage,
        ai_remarks=image.ai_remarks,
        analyzed_at=datetime.utcnow()
    )

@router.get("/results/{image_id}", response_model=AIAnalysisResult)
def get_analysis_results(
    image_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Get image record
    image = db.query(HealingImage).filter(HealingImage.id == image_id).first()
    
    if not image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image not found"
        )
    
    # Verify access
    patient = db.query(Patient).filter(Patient.id == image.patient_id).first()
    if current_user.role == "patient" and patient.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this analysis"
        )
    
    if not image.analyzed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Image has not been analyzed yet"
        )
    
    return AIAnalysisResult(
        image_id=image.id,
        healing_percentage=image.healing_percentage,
        ai_remarks=image.ai_remarks,
        analyzed_at=image.upload_date
    )

@router.get("/history/{patient_id}", response_model=List[AIAnalysisResult])
def get_healing_history(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Verify patient exists
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found"
        )
    
    # Verify access
    if current_user.role == "patient" and patient.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this history"
        )
    
    # Get all analyzed images for the patient
    images = db.query(HealingImage).filter(
        HealingImage.patient_id == patient_id,
        HealingImage.analyzed == True
    ).order_by(HealingImage.upload_date.asc()).all()
    
    history = [
        AIAnalysisResult(
            image_id=img.id,
            healing_percentage=img.healing_percentage,
            ai_remarks=img.ai_remarks,
            analyzed_at=img.upload_date
        )
        for img in images
    ]
    
    return history