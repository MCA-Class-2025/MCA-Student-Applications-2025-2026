import os
import uuid
from typing import List, Optional
from sqlalchemy.orm import Session
from fastapi import UploadFile, status
from pypdf import PdfReader
import docx

from app.config import settings
from app.models.document import Document
from app.models.user import User
from app.utils.exceptions import PrepGeniusException
from app.utils.logger import logger

class DocumentService:
    @staticmethod
    def extract_text_from_file(file_path: str, file_type: str) -> str:
        """Extract text content from PDF, DOCX, or TXT file."""
        extracted_text = ""
        try:
            if file_type == "pdf":
                reader = PdfReader(file_path)
                text_list = []
                for page in reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text_list.append(page_text)
                extracted_text = "\n\n".join(text_list)

            elif file_type == "docx":
                doc = docx.Document(file_path)
                paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
                extracted_text = "\n".join(paragraphs)

            elif file_type == "txt":
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    extracted_text = f.read()
            else:
                raise PrepGeniusException(f"Unsupported file type: {file_type}", status_code=400)

            return extracted_text.strip()
        except Exception as e:
            logger.error(f"Error extracting text from {file_path}: {e}")
            raise PrepGeniusException(
                message=f"Failed to extract text from document: {str(e)}",
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY
            )

    @staticmethod
    async def process_and_save_upload(db: Session, user: User, file: UploadFile) -> Document:
        """Validate, save on disk, extract text, and insert metadata into SQLite."""
        # 1. Validate file extension
        filename = file.filename or "uploaded_doc.txt"
        ext = filename.split(".")[-1].lower() if "." in filename else ""
        if ext not in settings.ALLOWED_EXTENSIONS:
            raise PrepGeniusException(
                message=f"File extension '.{ext}' is not allowed. Supported formats: PDF, DOCX, TXT.",
                status_code=status.HTTP_400_BAD_REQUEST
            )

        # 2. Read file content to check size
        content = await file.read()
        file_size = len(content)
        max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
        if file_size > max_bytes:
            raise PrepGeniusException(
                message=f"File size exceeds maximum limit of {settings.MAX_UPLOAD_SIZE_MB}MB.",
                status_code=status.HTTP_400_BAD_REQUEST
            )

        # 3. Save to disk
        user_upload_dir = os.path.join(settings.UPLOAD_DIR, str(user.id))
        os.makedirs(user_upload_dir, exist_ok=True)
        unique_name = f"{uuid.uuid4().hex}_{filename}"
        file_path = os.path.join(user_upload_dir, unique_name)

        with open(file_path, "wb") as f:
            f.write(content)

        # 4. Extract Text
        extracted_text = DocumentService.extract_text_from_file(file_path, ext)

        # 5. Insert Record into SQLite
        doc_record = Document(
            filename=filename,
            file_path=file_path,
            file_type=ext,
            file_size=file_size,
            char_count=len(extracted_text),
            extracted_text=extracted_text,
            status="processed",
            user_id=user.id
        )
        db.add(doc_record)
        db.commit()
        db.refresh(doc_record)

        logger.info(f"Successfully processed upload '{filename}' ({len(extracted_text)} chars) for User ID {user.id}")
        return doc_record

    @staticmethod
    def get_user_documents(db: Session, user_id: int) -> List[Document]:
        """Fetch upload history for a specific user."""
        return db.query(Document).filter(Document.user_id == user_id).order_by(Document.uploaded_at.desc()).all()

    @staticmethod
    def get_document_by_id(db: Session, user_id: int, doc_id: int) -> Optional[Document]:
        """Fetch single document details."""
        return db.query(Document).filter(Document.id == doc_id, Document.user_id == user_id).first()

    @staticmethod
    def delete_document(db: Session, user_id: int, doc_id: int) -> bool:
        """Delete document file and SQLite metadata record."""
        doc = DocumentService.get_document_by_id(db, user_id, doc_id)
        if not doc:
            return False

        if os.path.exists(doc.file_path):
            try:
                os.remove(doc.file_path)
            except Exception as e:
                logger.warning(f"Could not remove file {doc.file_path} from disk: {e}")

        db.delete(doc)
        db.commit()
        return True
