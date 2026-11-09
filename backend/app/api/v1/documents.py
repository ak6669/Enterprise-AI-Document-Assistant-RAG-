import hashlib
import os
import shutil
import uuid
from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.db.session import get_db
from app.models.database import Document, DocumentChunk
from app.schemas.document import DocumentResponse, DocumentDetailResponse, DocumentStatus, DocumentType
from app.services.document_parser import DocumentParser, DocumentParserError
from app.services.chunker import TextChunker
from app.services.embedding import EmbeddingService
from app.services.vector_store import VectorStoreService

router = APIRouter()

ALLOWED_EXTENSIONS = {"pdf", "docx", "txt", "text"}
MAX_FILE_BYTES = settings.MAX_FILE_SIZE_MB * 1024 * 1024


@router.post("/upload", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED, tags=["Documents"])
async def upload_document(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    """
    Uploads an enterprise document (PDF, DOCX, TXT), parses its text by page,
    chunks it, embeds it using Sentence Transformers, and indexes it into ChromaDB.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename cannot be empty.")

    ext = file.filename.split(".")[-1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"File extension '.{ext}' is not supported. Allowed formats: PDF, DOCX, TXT."
        )

    # Read file contents and validate size
    contents = await file.read()
    file_size = len(contents)
    if file_size > MAX_FILE_BYTES:
        raise HTTPException(
            status_code=400,
            detail=f"File size exceeds maximum limit of {settings.MAX_FILE_SIZE_MB}MB."
        )
    if file_size == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    # Calculate SHA-256 hash for deduplication
    file_hash = hashlib.sha256(contents).hexdigest()

    # Check for existing document with same hash
    existing_stmt = select(Document).where(Document.file_hash == file_hash)
    result = await db.execute(existing_stmt)
    existing_doc = result.scalar_one_or_none()
    if existing_doc and existing_doc.status == DocumentStatus.INDEXED.value:
        return existing_doc

    # Create document record
    doc_id = str(uuid.uuid4())
    upload_dir = Path(settings.UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)
    saved_file_path = upload_dir / f"{doc_id}_{file.filename}"

    with open(saved_file_path, "wb") as f:
        f.write(contents)

    doc_record = Document(
        id=doc_id,
        filename=file.filename,
        file_type=ext if ext in ["pdf", "docx", "txt"] else "txt",
        file_size=file_size,
        file_hash=file_hash,
        status=DocumentStatus.PROCESSING.value,
        storage_path=str(saved_file_path),
    )
    db.add(doc_record)
    await db.commit()
    await db.refresh(doc_record)

    try:
        # Step 1: Parse document
        parsed_doc = DocumentParser.parse(contents, file.filename)

        # Step 2: Page-preserving chunking
        chunker = TextChunker(chunk_size=settings.CHUNK_SIZE, chunk_overlap=settings.CHUNK_OVERLAP)
        chunks = chunker.chunk_document(parsed_doc, document_id=doc_id)

        if not chunks:
            raise DocumentParserError("No meaningful text chunks could be extracted from document.")

        # Step 3: Embed chunks
        chunk_texts = [c.content for c in chunks]
        embedding_service = EmbeddingService()
        embeddings = embedding_service.embed_texts(chunk_texts)

        # Step 4: Index into ChromaDB
        vector_store = VectorStoreService()
        vector_store.add_chunks(document_id=doc_id, chunks=chunks, embeddings=embeddings)

        # Step 5: Save chunk records to database
        db_chunks = [
            DocumentChunk(
                id=f"{doc_id}_chunk_{c.chunk_index}",
                document_id=doc_id,
                chunk_index=c.chunk_index,
                page_number=c.page_number,
                content=c.content,
                token_count=c.token_count,
            )
            for c in chunks
        ]
        db.add_all(db_chunks)

        # Update document record
        doc_record.status = DocumentStatus.INDEXED.value
        doc_record.page_count = parsed_doc.page_count
        doc_record.chunk_count = len(chunks)
        await db.commit()
        await db.refresh(doc_record)

        return doc_record

    except Exception as e:
        doc_record.status = DocumentStatus.FAILED.value
        doc_record.error_message = str(e)
        await db.commit()
        await db.refresh(doc_record)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process and index document: {str(e)}"
        )


@router.get("", response_model=List[DocumentResponse], tags=["Documents"])
async def list_documents(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """Lists all uploaded documents with status and metadata."""
    stmt = select(Document).order_by(Document.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/{document_id}", response_model=DocumentDetailResponse, tags=["Documents"])
async def get_document(
    document_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Retrieves document metadata along with all extracted chunks."""
    stmt = (
        select(Document)
        .options(selectinload(Document.chunks))
        .where(Document.id == document_id)
    )
    result = await db.execute(stmt)
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")
    return doc


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Documents"])
async def delete_document(
    document_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Deletes a document from relational database, ChromaDB, and disk."""
    stmt = select(Document).where(Document.id == document_id)
    result = await db.execute(stmt)
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")

    # Remove from ChromaDB
    vector_store = VectorStoreService()
    vector_store.delete_document_chunks(document_id)

    # Remove physical file
    if doc.storage_path and os.path.exists(doc.storage_path):
        try:
            os.remove(doc.storage_path)
        except OSError:
            pass

    # Remove from DB (cascade deletes chunks)
    await db.delete(doc)
    await db.commit()
    return None
