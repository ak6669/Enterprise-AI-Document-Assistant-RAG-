from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.core.config import settings
from app.db.session import get_db
from app.services.vector_store import VectorStoreService
from app.services.llm_service import LLMService

router = APIRouter()


@router.get("/health", tags=["Health"])
async def health_check(db: AsyncSession = Depends(get_db)):
    """Health check endpoint checking API, Database, and Vector Store status."""
    db_status = "connected"
    try:
        await db.execute(text("SELECT 1"))
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"

    vector_store = VectorStoreService()
    try:
        total_indexed_chunks = vector_store.count_chunks()
        vector_status = "healthy"
    except Exception as e:
        total_indexed_chunks = 0
        vector_status = f"unhealthy: {str(e)}"

    llm_service = LLMService()

    return {
        "status": "healthy" if db_status == "connected" and vector_status == "healthy" else "degraded",
        "version": settings.VERSION,
        "database": db_status,
        "vector_store": {
            "status": vector_status,
            "indexed_chunks": total_indexed_chunks,
        },
        "llm": {
            "configured": llm_service.is_configured,
            "model": settings.OPENAI_MODEL,
        },
        "embedding_model": settings.EMBEDDING_MODEL_NAME,
    }
