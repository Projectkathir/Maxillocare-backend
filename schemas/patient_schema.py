from pydantic import BaseModel
from datetime import date
from typing import Optional

class PatientBase(BaseModel):
    case_type: Optional[str] = None
    surgery_date: Optional[date] = None
    medical_history: Optional[str] = None
    doctor_id: Optional[int] = None

class PatientCreate(PatientBase):
    user_id: int

class PatientUpdate(PatientBase):
    current_healing_percentage: Optional[float] = None

class Patient(PatientBase):
    id: int
    user_id: int
    current_healing_percentage: float
    
    class Config:
        from_attributes = True

