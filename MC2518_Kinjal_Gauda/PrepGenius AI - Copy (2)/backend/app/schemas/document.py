from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class DocumentBase(BaseModel):
    filename: str
    file_type: str
    file_size: int

class DocumentResponse(DocumentBase):
    id: int
    char_count: int
    status: str
    uploaded_at: datetime
    extracted_text_preview: Optional[str] = None

    class Config:
        from_attributes = True

class DocumentDetailResponse(DocumentResponse):
    extracted_text: str
    file_path: str
