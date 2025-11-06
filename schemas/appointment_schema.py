from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class AppointmentBase(BaseModel):
    appointment_date: datetime
    notes: Optional[str] = None

class AppointmentCreate(AppointmentBase):
    patient_id: int
    doctor_id: int

class AppointmentUpdate(BaseModel):
    status: Optional[str] = None
    appointment_date: Optional[datetime] = None
    notes: Optional[str] = None

class Appointment(AppointmentBase):
    id: int
    patient_id: int
    doctor_id: int
    status: str
    created_at: datetime
    
    class Config:
        from_attributes = True