import logging
import time
import re
from typing import List, Dict, Any, Optional
from app.services.embedding import EmbeddingService
from app.services.vector_store import VectorStoreService
from app.services.llm_service import LLMService
from app.schemas.chat import Citation

logger = logging.getLogger(__name__)


class RAGService:
    """
    Core RAG Pipeline:
    1. Embeds incoming user query.
    2. Performs semantic retrieval against ChromaDB.
    3. Synthesizes grounded answer using OpenAI LLM.
    4. Resolves and structures source citations (Doc Name + Page Number).
    """

    def __init__(
        self,
        embedding_service: Optional[EmbeddingService] = None,
        vector_store: Optional[VectorStoreService] = None,
        llm_service: Optional[LLMService] = None
    ):
        self.embedding_service = embedding_service if embedding_service is not None else EmbeddingService()
        self.vector_store = vector_store if vector_store is not None else VectorStoreService()
        self.llm_service = llm_service if llm_service is not None else LLMService()

    def _extract_citations(
        self,
        answer: str,
        retrieved_chunks: List[Dict[str, Any]]
    ) -> List[Citation]:
        """
        Maps retrieved chunks into structured Citation objects.
        Matches inline citations such as [DocName, Page X] or attaches all retrieved sources.
        """
        citations: List[Citation] = []
        seen_keys = set()

        for chunk in retrieved_chunks:
            doc_id = chunk.get("document_id", "")
            filename = chunk.get("filename", "")
            page_num = chunk.get("page_number", 1)
            chunk_id = chunk.get("chunk_id", "")
            content = chunk.get("content", "")
            score = chunk.get("similarity_score", 0.0)

            key = (doc_id, page_num)
            if key not in seen_keys:
                seen_keys.add(key)
                # Create a concise excerpt (first 200 chars)
                clean_excerpt = content.strip().replace("\n", " ")
                if len(clean_excerpt) > 220:
                    clean_excerpt = clean_excerpt[:220] + "..."

                citations.append(Citation(
                    document_id=doc_id,
                    filename=filename,
                    page_number=page_num,
                    chunk_id=chunk_id,
                    excerpt=clean_excerpt,
                    score=score,
                ))

        return citations

    async def query(
        self,
        question: str,
        top_k: int = 4,
        document_ids: Optional[List[str]] = None,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """Executes the full RAG query cycle."""
        start_time = time.perf_counter()

        # Step 1: Embed query
        query_vector = self.embedding_service.embed_query(question)

        # Step 2: Retrieve relevant chunks
        chunks = self.vector_store.search(
            query_embedding=query_vector,
            top_k=top_k,
            document_ids=document_ids
        )

        # Step 3: Synthesize answer with LLM
        answer = await self.llm_service.generate_grounded_answer(
            query=question,
            context_chunks=chunks,
            conversation_history=conversation_history
        )

        # Step 4: Extract and resolve structured citations
        citations = self._extract_citations(answer, chunks)

        elapsed = round(time.perf_counter() - start_time, 3)

        return {
            "answer": answer,
            "citations": citations,
            "retrieved_chunks": chunks,
            "latency_seconds": elapsed,
        }
