from fastapi import APIRouter, Depends, UploadFile, File, status
from sqlalchemy.orm import Session
from typing import List

from app.database.session import get_db
from app.models.user import User
from app.schemas.document import DocumentResponse, DocumentDetailResponse
from app.services.document_service import DocumentService
from app.utils.deps import get_current_user
from app.utils.exceptions import PrepGeniusException

router = APIRouter(prefix="/documents", tags=["Document Upload & History"])

@router.post("/upload", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    doc = await DocumentService.process_and_save_upload(db, current_user, file)
    return DocumentResponse(
        id=doc.id,
        filename=doc.filename,
        file_type=doc.file_type,
        file_size=doc.file_size,
        char_count=doc.char_count,
        status=doc.status,
        uploaded_at=doc.uploaded_at,
        extracted_text_preview=doc.extracted_text[:200] if doc.extracted_text else ""
    )

@router.get("/history", response_model=List[DocumentResponse])
async def get_upload_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    docs = DocumentService.get_user_documents(db, current_user.id)
    return [
        DocumentResponse(
            id=d.id,
            filename=d.filename,
            file_type=d.file_type,
            file_size=d.file_size,
            char_count=d.char_count,
            status=d.status,
            uploaded_at=d.uploaded_at,
            extracted_text_preview=d.extracted_text[:200] if d.extracted_text else ""
        ) for d in docs
    ]

@router.get("/{doc_id}", response_model=DocumentDetailResponse)
async def get_document_details(
    doc_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    doc = DocumentService.get_document_by_id(db, current_user.id, doc_id)
    if not doc:
        raise PrepGeniusException("Document not found", status_code=404)
    return doc

@router.delete("/{doc_id}")
async def delete_document(
    doc_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    success = DocumentService.delete_document(db, current_user.id, doc_id)
    if not success:
        raise PrepGeniusException("Document not found or could not be deleted", status_code=404)
    return {"success": True, "message": "Document deleted successfully"}
