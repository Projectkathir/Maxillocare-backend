from sqlalchemy import Column, Integer, String, JSON, DateTime, ForeignKey
from datetime import datetime
from database import Base

class Questionnaire(Base):
    __tablename__ = "questionnaires"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    type = Column(String, nullable=False)  # pre_surgery, post_surgery
    questions = Column(JSON, nullable=False)  # [{id, question, type, options}]
    created_at = Column(DateTime, default=datetime.utcnow)


class QuestionnaireResponse(Base):
    __tablename__ = "questionnaire_responses"
    
    id = Column(Integer, primary_key=True, index=True)
    questionnaire_id = Column(Integer, ForeignKey("questionnaires.id"))
    patient_id = Column(Integer, ForeignKey("patients.id"))
    responses = Column(JSON, nullable=False)  # [{question_id, answer}]
    submitted_at = Column(DateTime, default=datetime.utcnow)