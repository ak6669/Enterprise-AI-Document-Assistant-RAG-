import os
from typing import List
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "Enterprise AI Document Assistant"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"

    # OpenAI API
    OPENAI_API_KEY: str = Field(default="", description="OpenAI API Key")
    OPENAI_MODEL: str = Field(default="gpt-4o-mini", description="OpenAI Model to use for RAG synthesis")
    OPENAI_TEMPERATURE: float = 0.0

    # Embeddings
    EMBEDDING_MODEL_NAME: str = Field(
        default="sentence-transformers/all-MiniLM-L6-v2",
        description="Sentence Transformer model for embedding generation"
    )

    # Database
    DATABASE_URL: str = Field(
        default="sqlite+aiosqlite:///./data/enterprise_rag.db",
        description="Database connection string (PostgreSQL for prod, SQLite for local dev)"
    )

    # ChromaDB
    CHROMA_PERSIST_DIRECTORY: str = Field(
        default="./data/chromadb",
        description="Directory for local persistent ChromaDB storage"
    )

    # Document Storage & Ingestion
    UPLOAD_DIR: str = Field(
        default="./data/uploads",
        description="Directory for storing uploaded files"
    )
    MAX_FILE_SIZE_MB: int = 50
    CHUNK_SIZE: int = 800
    CHUNK_OVERLAP: int = 150

    # Retrieval settings
    TOP_K_RETRIEVAL: int = 4
    SIMILARITY_THRESHOLD: float = 0.2

    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
