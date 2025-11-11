from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from database import get_db
from models.user import User
from models.questionnaire import Questionnaire, QuestionnaireResponse
from models.patient import Patient
from schemas.questionnaire_schema import (
    QuestionnaireCreate,
    Questionnaire as QuestionnaireSchema,
    QuestionnaireResponseCreate,
    QuestionnaireResponse as QuestionnaireResponseSchema
)
from utils.security import get_current_user, get_current_doctor

router = APIRouter()

# Questionnaire Management (Doctor only)

@router.post("/", response_model=QuestionnaireSchema, status_code=status.HTTP_201_CREATED)
def create_questionnaire(
    questionnaire_data: QuestionnaireCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_doctor)
):
    """Create a new questionnaire (Doctor only)"""
    new_questionnaire = Questionnaire(**questionnaire_data.dict())
    db.add(new_questionnaire)
    db.commit()
    db.refresh(new_questionnaire)
    return new_questionnaire


@router.get("/", response_model=List[QuestionnaireSchema])
def get_questionnaires(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all questionnaires (Both patient and doctor can access)"""
    questionnaires = db.query(Questionnaire).all()
    return questionnaires


@router.get("/{questionnaire_id}", response_model=QuestionnaireSchema)
def get_questionnaire(
    questionnaire_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific questionnaire by ID"""
    questionnaire = db.query(Questionnaire).filter(
        Questionnaire.id == questionnaire_id
    ).first()
    
    if not questionnaire:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Questionnaire not found"
        )
    
    return questionnaire


@router.put("/{questionnaire_id}", response_model=QuestionnaireSchema)
def update_questionnaire(
    questionnaire_id: int,
    questionnaire_data: QuestionnaireCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_doctor)
):
    """Update a questionnaire (Doctor only)"""
    questionnaire = db.query(Questionnaire).filter(
        Questionnaire.id == questionnaire_id
    ).first()
    
    if not questionnaire:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Questionnaire not found"
        )
    
    for key, value in questionnaire_data.dict().items():
        setattr(questionnaire, key, value)
    
    db.commit()
    db.refresh(questionnaire)
    return questionnaire


@router.delete("/{questionnaire_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_questionnaire(
    questionnaire_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_doctor)
):
    """Delete a questionnaire (Doctor only)"""
    questionnaire = db.query(Questionnaire).filter(
        Questionnaire.id == questionnaire_id
    ).first()
    
    if not questionnaire:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Questionnaire not found"
        )
    
    db.delete(questionnaire)
    db.commit()
    return None


# Questionnaire Responses

@router.post("/{questionnaire_id}/respond", response_model=QuestionnaireResponseSchema, status_code=status.HTTP_201_CREATED)
def submit_response(
    questionnaire_id: int,
    response_data: QuestionnaireResponseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Submit a questionnaire response"""
    # Verify questionnaire exists
    questionnaire = db.query(Questionnaire).filter(
        Questionnaire.id == questionnaire_id
    ).first()
    
    if not questionnaire:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Questionnaire not found"
        )
    
    # Verify patient exists
    patient = db.query(Patient).filter(
        Patient.id == response_data.patient_id
    ).first()
    
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found"
        )
    
    # If current user is patient, ensure they're responding for themselves
    if current_user.role == "patient":
        # Find patient record associated with this user
        user_patient = db.query(Patient).filter(Patient.user_id == current_user.id).first()
        if not user_patient or user_patient.id != response_data.patient_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Can only submit responses for yourself"
            )
    
    # Create response with questionnaire_id from URL
    new_response = QuestionnaireResponse(
        questionnaire_id=questionnaire_id,
        patient_id=response_data.patient_id,
        responses=response_data.responses
    )
    db.add(new_response)
    db.commit()
    db.refresh(new_response)
    
    return new_response


@router.get("/responses/patient/{patient_id}", response_model=List[QuestionnaireResponseSchema])
def get_patient_responses(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all responses for a specific patient"""
    # Verify patient exists
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found"
        )
    
    # Authorization check
    if current_user.role == "patient":
        user_patient = db.query(Patient).filter(Patient.user_id == current_user.id).first()
        if not user_patient or user_patient.id != patient_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view these responses"
            )
    
    responses = db.query(QuestionnaireResponse).filter(
        QuestionnaireResponse.patient_id == patient_id
    ).all()
    
    return responses


@router.get("/responses/{response_id}", response_model=QuestionnaireResponseSchema)
def get_response(
    response_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific response by ID"""
    response = db.query(QuestionnaireResponse).filter(
        QuestionnaireResponse.id == response_id
    ).first()
    
    if not response:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Response not found"
        )
    
    # Authorization check for patients
    if current_user.role == "patient":
        user_patient = db.query(Patient).filter(Patient.user_id == current_user.id).first()
        if not user_patient or response.patient_id != user_patient.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view this response"
            )
    
    return response
