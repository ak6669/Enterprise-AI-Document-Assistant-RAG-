from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field


class Citation(BaseModel):
    document_id: str
    filename: str
    page_number: int
    chunk_id: str
    excerpt: str
    score: float = 0.0


class ChatMessageRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000, description="The query message")
    conversation_id: Optional[str] = Field(default=None, description="Optional conversation UUID to continue a thread")
    top_k: Optional[int] = Field(default=4, ge=1, le=10, description="Number of context chunks to retrieve")
    document_ids: Optional[List[str]] = Field(default=None, description="Optional filter to scope retrieval to specific documents")


class ChatMessageResponse(BaseModel):
    conversation_id: str
    message_id: str
    query: str
    answer: str
    citations: List[Citation] = Field(default_factory=list)
    latency_seconds: float = 0.0
    created_at: datetime


class MessageItem(BaseModel):
    id: str
    conversation_id: str
    role: str
    content: str
    citations: List[Citation] = Field(default_factory=list)
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ConversationResponse(BaseModel):
    id: str
    title: str
    created_at: datetime
    updated_at: datetime
    messages: List[MessageItem] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)
