from datetime import datetime
from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field


class DocumentStatus(str, Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    INDEXED = "INDEXED"
    FAILED = "FAILED"


class DocumentType(str, Enum):
    PDF = "pdf"
    DOCX = "docx"
    TXT = "txt"


class DocumentBase(BaseModel):
    filename: str
    file_type: DocumentType
    file_size: int


class DocumentResponse(DocumentBase):
    id: str
    status: DocumentStatus
    page_count: int = 0
    chunk_count: int = 0
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DocumentChunkResponse(BaseModel):
    id: str
    document_id: str
    chunk_index: int
    page_number: int
    content: str
    token_count: int = 0

    model_config = ConfigDict(from_attributes=True)


class DocumentDetailResponse(DocumentResponse):
    chunks: List[DocumentChunkResponse] = Field(default_factory=list)
