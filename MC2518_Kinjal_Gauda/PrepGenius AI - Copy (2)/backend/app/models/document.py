from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database.session import Base

class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False) # Original file name
    file_path = Column(String, nullable=False) # Storage path on disk
    file_type = Column(String, nullable=False) # pdf, docx, txt
    file_size = Column(Integer, nullable=False) # Size in bytes
    char_count = Column(Integer, default=0) # Number of extracted characters
    extracted_text = Column(Text, nullable=True) # Full extracted text content
    status = Column(String, default="processed") # processed, error, uploading
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    owner = relationship("User", back_populates="documents")
