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
    QuestionnaireResponse as QuestionnaireResponseSchema,
    QuestionnaireResponseDetailed  # NEW IMPORT
)
from utils.security import get_current_user, get_current_doctor

router = APIRouter()

# ============================================================================
# QUESTIONNAIRE MANAGEMENT (Doctor only)
# ============================================================================

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


# ============================================================================
# QUESTIONNAIRE RESPONSES - Patient Submission
# ============================================================================

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


# ============================================================================
# BASIC RESPONSE RETRIEVAL (Original endpoints)
# ============================================================================

@router.get("/responses/patient/{patient_id}", response_model=List[QuestionnaireResponseSchema])
def get_patient_responses(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all responses for a specific patient (basic format)"""
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


# ============================================================================
# NEW ENDPOINTS - DETAILED RESPONSES FOR DOCTORS
# ============================================================================

@router.get(
    "/responses/patient/{patient_id}/detailed",
    response_model=List[QuestionnaireResponseDetailed],
    summary="Get detailed questionnaire responses for a patient (Doctor view)",
    tags=["Doctor - Patient Responses"]
)
def get_patient_responses_detailed(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_doctor)  # Only doctors can access
):
    """
    📋 **Get all questionnaire responses for a specific patient WITH question details**
    
    **This endpoint is designed specifically for doctors to review patient answers.**
    
    **Returns:**
    - ✅ Questionnaire title and type
    - ✅ All original questions
    - ✅ Patient's answers matched to questions
    - ✅ Patient's name
    - ✅ Submission timestamp
    
    **Authorization:** Doctors only
    
    **Use Case:** Doctor clicks on a patient to see all their questionnaire responses
    """
    
    # 1. Verify patient exists
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Patient with ID {patient_id} not found"
        )
    
    # 2. Get patient's user info (for name)
    patient_user = db.query(User).filter(User.id == patient.user_id).first()
    patient_name = patient_user.full_name if patient_user else "Unknown Patient"
    
    # 3. Get all responses for this patient with questionnaire details (JOIN)
    responses = (
        db.query(QuestionnaireResponse, Questionnaire)
        .join(Questionnaire, QuestionnaireResponse.questionnaire_id == Questionnaire.id)
        .filter(QuestionnaireResponse.patient_id == patient_id)
        .order_by(QuestionnaireResponse.submitted_at.desc())  # Most recent first
        .all()
    )
    
    if not responses:
        return []  # Return empty list if patient hasn't answered any questionnaires
    
    # 4. Format the response data
    detailed_responses = []
    for response, questionnaire in responses:
        detailed_responses.append({
            "response_id": response.id,
            "patient_id": patient_id,
            "patient_name": patient_name,
            "questionnaire_id": questionnaire.id,
            "questionnaire_title": questionnaire.title,
            "questionnaire_type": questionnaire.type,
            "questions": questionnaire.questions,  # Original questions
            "responses": response.responses,  # Patient's answers
            "submitted_at": response.submitted_at
        })
    
    return detailed_responses


@router.get(
    "/responses/my-patients",
    response_model=List[QuestionnaireResponseDetailed],
    summary="Get all questionnaire responses for doctor's patients",
    tags=["Doctor - Patient Responses"]
)
def get_my_patients_responses(
    questionnaire_type: str = None,  # Optional filter by type (pre_surgery, post_surgery, etc.)
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_doctor)
):
    """
    📊 **Get all questionnaire responses for ALL patients assigned to this doctor**
    
    **This is useful for a dashboard view where doctors can see all their patients' responses.**
    
    **Returns:**
    - ✅ All responses from all assigned patients
    - ✅ Each response includes patient name, questions, and answers
    - ✅ Sorted by most recent first
    
    **Optional Filter:**
    - `questionnaire_type`: Filter by type (e.g., "pre_surgery", "post_surgery")
    
    **Authorization:** Doctors only
    
    **Use Case:** Doctor dashboard showing all patient responses at a glance
    """
    
    # 1. Get all patients assigned to this doctor
    my_patients = db.query(Patient).filter(Patient.doctor_id == current_user.id).all()
    
    if not my_patients:
        return []  # No patients assigned yet
    
    patient_ids = [p.id for p in my_patients]
    
    # 2. Build query for responses
    query = (
        db.query(QuestionnaireResponse, Questionnaire, Patient, User)
        .join(Questionnaire, QuestionnaireResponse.questionnaire_id == Questionnaire.id)
        .join(Patient, QuestionnaireResponse.patient_id == Patient.id)
        .join(User, Patient.user_id == User.id)
        .filter(QuestionnaireResponse.patient_id.in_(patient_ids))
    )
    
    # 3. Apply optional filter
    if questionnaire_type:
        query = query.filter(Questionnaire.type == questionnaire_type)
    
    # 4. Execute query and order results
    responses = query.order_by(QuestionnaireResponse.submitted_at.desc()).all()
    
    if not responses:
        return []  # No responses yet
    
    # 5. Format the response data
    detailed_responses = []
    for response, questionnaire, patient, user in responses:
        detailed_responses.append({
            "response_id": response.id,
            "patient_id": patient.id,
            "patient_name": user.full_name,
            "questionnaire_id": questionnaire.id,
            "questionnaire_title": questionnaire.title,
            "questionnaire_type": questionnaire.type,
            "questions": questionnaire.questions,
            "responses": response.responses,
            "submitted_at": response.submitted_at
        })
    
    return detailed_responses
