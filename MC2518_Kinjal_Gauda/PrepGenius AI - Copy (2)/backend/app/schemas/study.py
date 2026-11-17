from pydantic import BaseModel
from typing import List, Optional, Dict, Any

class SummarizeRequest(BaseModel):
    document_ids: Optional[List[int]] = None
    raw_text: Optional[str] = None
    summary_mode: str = "quick" # quick, detailed, bullet, keypoints, definitions
    language: str = "English" # English, Hindi, Marathi

class FlashcardsRequest(BaseModel):
    document_ids: Optional[List[int]] = None
    raw_text: Optional[str] = None
    count: int = 5

class FlashcardItem(BaseModel):
    id: int
    question: str
    answer: str
    difficulty: str = "medium"

class MCQRequest(BaseModel):
    document_ids: Optional[List[int]] = None
    raw_text: Optional[str] = None
    count: int = 5

class MCQItem(BaseModel):
    id: int
    question: str
    options: List[str]
    correct_option: int
    explanation: str

class RevisionNotesRequest(BaseModel):
    document_ids: Optional[List[int]] = None
    raw_text: Optional[str] = None
    language: str = "English"

class StudyPlannerRequest(BaseModel):
    document_ids: Optional[List[int]] = None
    days_until_exam: int = 7

class AnalyticsResponse(BaseModel):
    uploaded_notes_count: int
    total_characters_processed: int
    questions_asked_count: int
    study_time_hours: float
    quiz_accuracy_percentage: float
    exam_readiness_score: float
