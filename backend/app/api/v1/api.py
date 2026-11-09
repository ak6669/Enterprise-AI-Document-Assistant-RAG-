from fastapi import APIRouter
from app.api.v1.health import router as health_router
from app.api.v1.documents import router as documents_router
from app.api.v1.chat import router as chat_router

api_router = APIRouter()

api_router.include_router(health_router, prefix="", tags=["Health"])
api_router.include_router(documents_router, prefix="/documents", tags=["Documents"])
api_router.include_router(chat_router, prefix="/chat", tags=["Chat"])
