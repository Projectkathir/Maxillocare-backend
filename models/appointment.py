from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from database import Base
from datetime import datetime

class Appointment(Base):
    __tablename__ = "appointments"
    
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"))
    doctor_id = Column(Integer, ForeignKey("users.id"))
    appointment_date = Column(DateTime, nullable=False)
    status = Column(String, default="pending")  # pending, approved, cancelled
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
