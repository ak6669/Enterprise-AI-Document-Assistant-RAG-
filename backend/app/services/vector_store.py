import logging
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings as ChromaSettings
from app.core.config import settings
from app.services.chunker import TextChunk

logger = logging.getLogger(__name__)


class VectorStoreService:
    """
    Manages vector indexing and semantic retrieval using ChromaDB.
    Maintains embeddings, chunk text, and strict source metadata (Doc name, Page number).
    """

    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, persist_directory: Optional[str] = None):
        persist_dir = persist_directory or settings.CHROMA_PERSIST_DIRECTORY
        Path(persist_dir).mkdir(parents=True, exist_ok=True)
        self.persist_dir = persist_dir

        self.client = chromadb.PersistentClient(
            path=self.persist_dir,
            settings=ChromaSettings(anonymized_telemetry=False)
        )
        self.collection_name = "enterprise_rag_chunks"
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"}
        )
        logger.info(f"Initialized ChromaDB vector store at: {self.persist_dir}")

    def add_chunks(
        self,
        document_id: str,
        chunks: List[TextChunk],
        embeddings: List[List[float]]
    ) -> int:
        """Indexes text chunks and their embeddings into ChromaDB."""
        if not chunks:
            return 0

        ids: List[str] = []
        documents: List[str] = []
        metadatas: List[Dict[str, Any]] = []

        for idx, chunk in enumerate(chunks):
            chunk_id = f"{document_id}_chunk_{chunk.chunk_index}"
            ids.append(chunk_id)
            documents.append(chunk.content)
            metadatas.append({
                "document_id": document_id,
                "filename": chunk.metadata.get("filename", "unknown"),
                "file_type": chunk.metadata.get("file_type", "txt"),
                "page_number": int(chunk.page_number),
                "chunk_index": int(chunk.chunk_index),
                "token_count": int(chunk.token_count),
            })

        self.collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas,
        )
        logger.info(f"Indexed {len(chunks)} chunks for document {document_id}")
        return len(chunks)

    def search(
        self,
        query_embedding: List[float],
        top_k: int = 4,
        document_ids: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Queries ChromaDB for the most semantically relevant chunks.
        Returns chunk content, metadata (including page number and document name), and similarity score.
        """
        if not query_embedding:
            return []

        where_filter = None
        if document_ids and len(document_ids) == 1:
            where_filter = {"document_id": document_ids[0]}
        elif document_ids and len(document_ids) > 1:
            where_filter = {"document_id": {"$in": document_ids}}

        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=where_filter,
            include=["documents", "metadatas", "distances"]
        )

        retrieved: List[Dict[str, Any]] = []
        if not results or not results["ids"] or not results["ids"][0]:
            return retrieved

        ids = results["ids"][0]
        docs = results["documents"][0] if results["documents"] else []
        metas = results["metadatas"][0] if results["metadatas"] else []
        distances = results["distances"][0] if results["distances"] else []

        for i in range(len(ids)):
            # For cosine space in Chroma, distance is (1 - cosine_similarity).
            # Convert distance to similarity score in [0, 1]
            dist = distances[i] if i < len(distances) else 1.0
            similarity_score = max(0.0, min(1.0, 1.0 - dist))

            meta = metas[i] if i < len(metas) else {}
            retrieved.append({
                "chunk_id": ids[i],
                "content": docs[i] if i < len(docs) else "",
                "document_id": meta.get("document_id", ""),
                "filename": meta.get("filename", "unknown"),
                "page_number": int(meta.get("page_number", 1)),
                "chunk_index": int(meta.get("chunk_index", 0)),
                "similarity_score": round(similarity_score, 4),
            })

        return retrieved

    def delete_document_chunks(self, document_id: str) -> bool:
        """Deletes all chunks associated with a specific document ID."""
        try:
            self.collection.delete(where={"document_id": document_id})
            logger.info(f"Deleted chunks for document {document_id} from vector store.")
            return True
        except Exception as e:
            logger.error(f"Error deleting chunks for document {document_id}: {e}")
            return False

    def count_chunks(self) -> int:
        """Returns total chunks stored in the vector database."""
        return self.collection.count()
