from pydantic import BaseModel
from datetime import datetime

class MessageBase(BaseModel):
    receiver_id: int
    patient_id: int
    message: str

class MessageCreate(MessageBase):
    pass

class Message(MessageBase):
    id: int
    sender_id: int
    is_read: bool
    sent_at: datetime
    
    class Config:
        from_attributes = True