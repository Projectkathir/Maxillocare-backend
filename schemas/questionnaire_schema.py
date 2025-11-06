from pydantic import BaseModel
from datetime import datetime
from typing import List, Dict, Any

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
