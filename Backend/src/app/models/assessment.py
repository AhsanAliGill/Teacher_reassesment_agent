from datetime import datetime
from typing import List, Optional
from sqlmodel import SQLModel, Field, Relationship
import uuid

# Association table for many-to-many relationship between assessments and questions
class AssessmentQuestionLink(SQLModel, table=True):
    assessment_id: uuid.UUID = Field(foreign_key="assessment.id", primary_key=True)
    question_id: uuid.UUID = Field(foreign_key="question.id", primary_key=True)

class Question(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    question_text: str
    marks: float
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    assessments: List["Assessment"] = Relationship(back_populates="questions", link_model=AssessmentQuestionLink)

class Assessment(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    subject_name: str
    file_name: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    questions: List[Question] = Relationship(back_populates="assessments", link_model=AssessmentQuestionLink)

# Pydantic models for request/response
class QuestionBase(SQLModel):
    question_text: str
    marks: float

class QuestionCreate(QuestionBase):
    pass

class QuestionInDB(QuestionBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class AssessmentBase(SQLModel):
    subject_name: str
    file_name: Optional[str] = None

class AssessmentCreate(AssessmentBase):
    questions: List[QuestionBase]

class AssessmentInDB(AssessmentBase):
    id: uuid.UUID
    questions: List[QuestionInDB] = []
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
