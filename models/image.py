from sqlalchemy import Column, Integer, String, Text, DateTime, Float, Boolean, ForeignKey
from datetime import datetime
from database import Base


class HealingImage(Base):
    __tablename__ = "healing_images"
    
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"))
    image_path = Column(String, nullable=False)
    upload_date = Column(DateTime, default=datetime.utcnow)
    healing_percentage = Column(Float, nullable=True)
    ai_remarks = Column(Text, nullable=True)
    analyzed = Column(Boolean, default=False)
    
    # NEW FIELDS - Medical classification and recommendations
    fracture_classification = Column(String, nullable=True)
    recommended_actions = Column(Text, nullable=True)
