

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class ChatRequest(BaseModel):

    message: str = Field(..., min_length=1, max_length=2000)
    session_id: Optional[str] = Field(None, description="Chat session ID")

class SourceDocument(BaseModel):

    content: str
    source_file: str = Field(..., description="The filename or identifier of the source")
    chunk_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    score: Optional[float] = None
    related_images: Optional[List[str]] = Field(default_factory=list, description="List of related image URLs or paths")

class ChatResponse(BaseModel):

    message: str
    sources: List[SourceDocument] = []
    related_images: List[str] = []
    session_id: str
    message_id: str
    timestamp: datetime

class ChatSessionCreate(BaseModel):

    session_name: Optional[str] = "New Chat"

class ChatSessionResponse(BaseModel):

    id: str
    session_name: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class ChatMessageResponse(BaseModel):

    id: str
    session_id: str
    role: str
    content: str
    sources: List[SourceDocument] = []
    created_at: datetime

    class Config:
        from_attributes = True

class ChatHistoryResponse(BaseModel):

    session: ChatSessionResponse
    messages: List[ChatMessageResponse]

class HealthResponse(BaseModel):

    status: str
    timestamp: datetime
    version: str
    services: Dict[str, str]

class ErrorResponse(BaseModel):

    detail: str
    error_type: Optional[str] = None
    timestamp: datetime