from sqlalchemy import Column, Integer, String, Text, Date, Float, ForeignKey
from database import Base

class Patient(Base):
    __tablename__ = "patients"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    case_type = Column(String)
    surgery_date = Column(Date, nullable=True)
    medical_history = Column(Text)
    doctor_id = Column(Integer, ForeignKey("users.id"))
    current_healing_percentage = Column(Float, default=0.0)