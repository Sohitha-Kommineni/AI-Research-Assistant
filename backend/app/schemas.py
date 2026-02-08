from datetime import datetime
from typing import Any, List, Optional

from pydantic import BaseModel, EmailStr, Field


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    email: EmailStr


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)


class UserOut(BaseModel):
    id: int
    email: EmailStr
    created_at: datetime

    class Config:
        from_attributes = True


class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = None


class ProjectOut(BaseModel):
    id: int
    name: str
    description: Optional[str]
    created_at: datetime
    last_activity_at: datetime
    document_count: int = 0

    class Config:
        from_attributes = True


class DocumentOut(BaseModel):
    id: int
    name: str
    doc_type: str
    status: str
    source_url: Optional[str]
    metadata_json: Optional[dict]
    text_excerpt: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class ChatRequest(BaseModel):
    question: str


class Citation(BaseModel):
    document_id: int
    document_name: str
    page_number: Optional[int]
    snippet: str


class ChatResponse(BaseModel):
    answer: str
    citations: List[Citation]
    used_chunks: Optional[List[dict]] = None


class ChatMessageOut(BaseModel):
    id: int
    role: str
    content: str
    sources_json: Optional[List[dict]]
    created_at: datetime

    class Config:
        from_attributes = True


class DocumentTextResponse(BaseModel):
    document_id: int
    text: str
    metadata: Optional[dict]


class IngestUrlRequest(BaseModel):
    url: str
