from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class HealingImageBase(BaseModel):
    patient_id: int

class HealingImageCreate(HealingImageBase):
    image_path: str

class HealingImage(HealingImageBase):
    id: int
    image_path: str
    upload_date: datetime
    healing_percentage: Optional[float] = None
    ai_remarks: Optional[str] = None
    analyzed: bool
    
    class Config:
        from_attributes = True

class AIAnalysisResult(BaseModel):
    image_id: int
    healing_percentage: float
    ai_remarks: str
    analyzed_at: datetime