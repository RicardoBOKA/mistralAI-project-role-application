"""Pydantic schemas for API requests and responses."""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class MessageRole(str, Enum):
    """Message role in conversation."""

    USER = "user"
    ASSISTANT = "assistant"


class ChatMessage(BaseModel):
    """A single message in the conversation."""

    role: MessageRole
    content: str


class SourceChunk(BaseModel):
    """A source chunk used for generating the response."""

    document_id: str
    document_name: str
    chunk_index: int
    content: str
    score: float = Field(ge=0, le=1, description="Similarity score")


class ChatRequest(BaseModel):
    """Request body for chat endpoint."""

    message: str = Field(min_length=1, max_length=10000)
    history: list[ChatMessage] = Field(default_factory=list)


class ChatResponse(BaseModel):
    """Response from chat endpoint (non-streaming)."""

    answer: str
    sources: list[SourceChunk]


class DocumentInfo(BaseModel):
    """Information about an uploaded document."""

    id: str
    filename: str
    file_type: str
    chunk_count: int
    uploaded_at: datetime
    file_size: int  # in bytes


class DocumentUploadResponse(BaseModel):
    """Response after document upload."""

    document: DocumentInfo
    message: str


class DocumentListResponse(BaseModel):
    """Response for listing documents."""

    documents: list[DocumentInfo]
    total: int
