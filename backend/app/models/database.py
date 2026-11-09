import json
import uuid
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import (
    Column,
    String,
    Integer,
    Text,
    DateTime,
    ForeignKey,
    Index
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


def get_utc_now():
    return datetime.now(timezone.utc)


class Document(Base):
    __tablename__ = "documents"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    filename = Column(String(255), nullable=False)
    file_type = Column(String(10), nullable=False)  # pdf, docx, txt
    file_size = Column(Integer, nullable=False)
    file_hash = Column(String(64), nullable=True, index=True)
    status = Column(String(20), nullable=False, default="PENDING", index=True)
    error_message = Column(Text, nullable=True)
    page_count = Column(Integer, default=0)
    chunk_count = Column(Integer, default=0)
    storage_path = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), default=get_utc_now)
    updated_at = Column(DateTime(timezone=True), default=get_utc_now, onupdate=get_utc_now)

    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    chunk_index = Column(Integer, nullable=False)
    page_number = Column(Integer, nullable=False, default=1)
    content = Column(Text, nullable=False)
    token_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), default=get_utc_now)

    document = relationship("Document", back_populates="chunks")

    __table_args__ = (
        Index("ix_doc_page", "document_id", "page_number"),
    )


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(255), nullable=False, default="New Conversation")
    created_at = Column(DateTime(timezone=True), default=get_utc_now)
    updated_at = Column(DateTime(timezone=True), default=get_utc_now, onupdate=get_utc_now)

    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan", order_by="Message.created_at")


class Message(Base):
    __tablename__ = "messages"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    conversation_id = Column(String(36), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(String(20), nullable=False)  # user, assistant, system
    content = Column(Text, nullable=False)
    citations_json = Column(Text, nullable=True)  # JSON-encoded string
    created_at = Column(DateTime(timezone=True), default=get_utc_now)

    conversation = relationship("Conversation", back_populates="messages")

    @property
    def citations(self) -> List[dict]:
        if not self.citations_json:
            return []
        try:
            return json.loads(self.citations_json)
        except Exception:
            return []

    @citations.setter
    def citations(self, value: List[dict]):
        self.citations_json = json.dumps(value) if value else None
