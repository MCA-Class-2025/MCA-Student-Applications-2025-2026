from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class ChatMessageBase(BaseModel):
    role: str # user or assistant
    content: str

class SourceCitation(BaseModel):
    filename: str
    chunk_index: int
    relevance_score: float
    snippet: str

class ChatMessageResponse(ChatMessageBase):
    id: int
    created_at: datetime
    citations: Optional[List[SourceCitation]] = None

    class Config:
        from_attributes = True

class ChatSessionCreate(BaseModel):
    title: Optional[str] = "New Study Session"

class ChatSessionResponse(BaseModel):
    id: int
    title: str
    created_at: datetime
    message_count: int = 0

    class Config:
        from_attributes = True

class RAGQueryRequest(BaseModel):
    session_id: int
    query: str
    document_ids: Optional[List[int]] = None # Optional list of specific documents to filter RAG context
