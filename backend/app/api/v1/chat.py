import json
import uuid
from typing import List
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.db.session import get_db
from app.models.database import Conversation, Message
from app.schemas.chat import (
    ChatMessageRequest,
    ChatMessageResponse,
    ConversationResponse,
    MessageItem,
    Citation,
)
from app.services.rag_service import RAGService

router = APIRouter()


@router.post("", response_model=ChatMessageResponse, tags=["Chat"])
async def send_chat_message(
    payload: ChatMessageRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Submits a user query to the RAG pipeline.
    Retrieves grounded context from ChromaDB, queries OpenAI, and returns an answer with
    verifiable source citations including document name and page number.
    """
    # 1. Resolve or create conversation
    conv_id = payload.conversation_id
    if conv_id:
        stmt = select(Conversation).where(Conversation.id == conv_id)
        result = await db.execute(stmt)
        conversation = result.scalar_one_or_none()
        if not conversation:
            conversation = Conversation(id=conv_id, title=payload.message[:40])
            db.add(conversation)
    else:
        conv_id = str(uuid.uuid4())
        conversation = Conversation(id=conv_id, title=payload.message[:40])
        db.add(conversation)

    await db.commit()
    await db.refresh(conversation)

    # 2. Fetch past conversation turns for dialogue context
    history_stmt = (
        select(Message)
        .where(Message.conversation_id == conv_id)
        .order_by(Message.created_at.asc())
        .limit(6)
    )
    history_result = await db.execute(history_stmt)
    history_turns = []
    for m in history_result.scalars().all():
        history_turns.append({"role": m.role, "content": m.content})

    # 3. Store user message in database
    user_msg_id = str(uuid.uuid4())
    user_message = Message(
        id=user_msg_id,
        conversation_id=conv_id,
        role="user",
        content=payload.message,
    )
    db.add(user_message)
    await db.commit()

    # 4. Execute RAG query
    rag_service = RAGService()
    rag_output = await rag_service.query(
        question=payload.message,
        top_k=payload.top_k or 4,
        document_ids=payload.document_ids,
        conversation_history=history_turns,
    )

    # 5. Store assistant message in database
    assistant_msg_id = str(uuid.uuid4())
    citations_data = [c.model_dump() for c in rag_output["citations"]]

    assistant_message = Message(
        id=assistant_msg_id,
        conversation_id=conv_id,
        role="assistant",
        content=rag_output["answer"],
        citations_json=json.dumps(citations_data),
    )
    db.add(assistant_message)
    await db.commit()

    return ChatMessageResponse(
        conversation_id=conv_id,
        message_id=assistant_msg_id,
        query=payload.message,
        answer=rag_output["answer"],
        citations=rag_output["citations"],
        latency_seconds=rag_output["latency_seconds"],
        created_at=datetime.now(timezone.utc),
    )


@router.get("/conversations", response_model=List[ConversationResponse], tags=["Chat"])
async def list_conversations(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=50),
    db: AsyncSession = Depends(get_db)
):
    """Lists recent conversation sessions with their message history."""
    stmt = (
        select(Conversation)
        .options(selectinload(Conversation.messages))
        .order_by(Conversation.updated_at.desc())
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(stmt)
    convs = result.scalars().all()
    
    responses = []
    for c in convs:
        msg_items = [
            MessageItem(
                id=m.id,
                conversation_id=m.conversation_id,
                role=m.role,
                content=m.content,
                citations=[Citation(**item) for item in m.citations],
                created_at=m.created_at,
            )
            for m in c.messages
        ]
        responses.append(ConversationResponse(
            id=c.id,
            title=c.title,
            created_at=c.created_at,
            updated_at=c.updated_at,
            messages=msg_items,
        ))
    return responses


@router.get("/conversations/{conversation_id}", response_model=ConversationResponse, tags=["Chat"])
async def get_conversation(
    conversation_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Retrieves a single conversation by ID with all messages and citations."""
    stmt = (
        select(Conversation)
        .options(selectinload(Conversation.messages))
        .where(Conversation.id == conversation_id)
    )
    result = await db.execute(stmt)
    conv = result.scalar_one_or_none()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found.")

    msg_items = [
        MessageItem(
            id=m.id,
            conversation_id=m.conversation_id,
            role=m.role,
            content=m.content,
            citations=[Citation(**item) for item in m.citations],
            created_at=m.created_at,
        )
        for m in conv.messages
    ]
    return ConversationResponse(
        id=conv.id,
        title=conv.title,
        created_at=conv.created_at,
        updated_at=conv.updated_at,
        messages=msg_items,
    )


@router.delete("/conversations/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Chat"])
async def delete_conversation(
    conversation_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Deletes a conversation session and all its messages."""
    stmt = select(Conversation).where(Conversation.id == conversation_id)
    result = await db.execute(stmt)
    conv = result.scalar_one_or_none()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found.")
    await db.delete(conv)
    await db.commit()
    return None
