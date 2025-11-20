from pydantic import BaseModel
from datetime import datetime
from typing import List, Dict, Any, Optional


class QuestionnaireBase(BaseModel):
    title: str
    type: str
    questions: List[Dict[str, Any]]


class QuestionnaireCreate(QuestionnaireBase):
    pass


class Questionnaire(QuestionnaireBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class QuestionnaireResponseCreate(BaseModel):
    questionnaire_id: int
    patient_id: int
    responses: List[Dict[str, Any]]


class QuestionnaireResponse(QuestionnaireResponseCreate):
    id: int
    submitted_at: datetime
    
    class Config:
        from_attributes = True


# ========================================
# NEW SCHEMA - Enhanced Response for Doctors
# ========================================
class QuestionnaireResponseDetailed(BaseModel):
    """
    Detailed response schema that includes questionnaire info.
    This is what doctors need to see - questions AND answers together.
    
    Example usage:
    - Doctor views all responses for a specific patient
    - Doctor dashboard showing all patient responses
    """
    response_id: int
    patient_id: int
    patient_name: Optional[str] = None  # Patient's full name from User table
    questionnaire_id: int
    questionnaire_title: str
    questionnaire_type: str  # pre_surgery, post_surgery, follow_up, etc.
    questions: List[Dict[str, Any]]  # Original questions from questionnaire
    responses: List[Dict[str, Any]]  # Patient's answers matched to questions
    submitted_at: datetime
    
    class Config:
        from_attributes = True
