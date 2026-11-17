from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any

from app.database.session import get_db
from app.models.user import User
from app.schemas.study import (
    SummarizeRequest,
    FlashcardsRequest,
    FlashcardItem,
    MCQRequest,
    MCQItem,
    RevisionNotesRequest,
    StudyPlannerRequest,
    AnalyticsResponse,
)
from app.services.study_service import StudyService
from app.utils.deps import get_current_user
from app.utils.exceptions import PrepGeniusException

router = APIRouter(prefix="/study", tags=["Smart AI Study Generators & Analytics"])

@router.post("/summarize")
async def generate_summary(
    payload: SummarizeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    summary = await StudyService.generate_summary(
        db, current_user.id, payload.document_ids or [], payload.raw_text or "", payload.summary_mode, payload.language
    )
    return {"summary": summary, "mode": payload.summary_mode, "language": payload.language}

@router.post("/flashcards", response_model=List[FlashcardItem])
async def generate_flashcards(
    payload: FlashcardsRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    cards = await StudyService.generate_flashcards(
        db, current_user.id, payload.document_ids or [], payload.raw_text or "", payload.count
    )
    return cards

@router.post("/mcqs", response_model=List[MCQItem])
async def generate_mcqs(
    payload: MCQRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    mcqs = await StudyService.generate_mcqs(
        db, current_user.id, payload.document_ids or [], payload.raw_text or "", payload.count
    )
    return mcqs

@router.post("/revision-notes")
async def generate_revision_notes(
    payload: RevisionNotesRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    notes = await StudyService.generate_revision_notes(
        db, current_user.id, payload.document_ids or [], payload.raw_text or "", payload.language
    )
    return {"notes": notes, "language": payload.language}

@router.post("/planner")
async def generate_planner(
    payload: StudyPlannerRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    plan = await StudyService.generate_planner(
        db, current_user.id, payload.document_ids or [], payload.days_until_exam
    )
    return plan

@router.get("/analytics", response_model=AnalyticsResponse)
async def get_study_analytics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    analytics = StudyService.calculate_analytics(db, current_user.id)
    return analytics

@router.post("/fused-plan/{student_id}")
async def generate_fused_study_plan(student_id: str):
    """Generate a personalized LLM Study Plan based on the dynamic wide fused student profile."""
    result = await StudyService.generate_fused_study_plan(student_id)
    if not result:
        raise PrepGeniusException(
            message=f"Student with Student_ID '{student_id}' not found.",
            status_code=status.HTTP_404_NOT_FOUND,
            details={"student_id": student_id}
        )
    return result
