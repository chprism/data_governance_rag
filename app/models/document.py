"""
Document model for the application.
"""
from datetime import datetime
from pydantic import BaseModel, Field
from typing import List, Optional


class Document(BaseModel):
    """Document model for storing document metadata."""
    id: Optional[str] = None
    filename: str
    content_type: str
    size: int
    upload_date: datetime = Field(default_factory=datetime.now)
    chunks: Optional[List[str]] = None
    vector_ids: Optional[List[str]] = None
    
    class Config:
        arbitrary_types_allowed = True


class DocumentChunk(BaseModel):
    """Document chunk model for storing document chunks."""
    id: Optional[str] = None
    document_id: str
    content: str
    metadata: dict
    embedding: Optional[List[float]] = None
