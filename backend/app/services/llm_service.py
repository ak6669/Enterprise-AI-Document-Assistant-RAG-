import logging
import os
from typing import List, Dict, Any, Optional
from openai import OpenAI, AsyncOpenAI
from app.core.config import settings

logger = logging.getLogger(__name__)


class LLMService:
    """
    OpenAI LLM Integration service.
    Implements strict context grounding and hallucination prevention.
    """

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or settings.OPENAI_API_KEY or os.environ.get("OPENAI_API_KEY", "")
        self.model = model or settings.OPENAI_MODEL
        self.temperature = settings.OPENAI_TEMPERATURE
        
        self.client: Optional[AsyncOpenAI] = None
        if self.api_key and not self.api_key.startswith("your-"):
            self.client = AsyncOpenAI(api_key=self.api_key)

    @property
    def is_configured(self) -> bool:
        return bool(self.client and self.api_key)

    async def generate_grounded_answer(
        self,
        query: str,
        context_chunks: List[Dict[str, Any]],
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> str:
        """
        Generates an answer strictly grounded in the provided context chunks.
        Every factual claim must cite [DocumentName, Page X].
        """
        if not context_chunks:
            return (
                "I could not find any relevant information in the uploaded documents to answer your query. "
                "Please make sure you have uploaded relevant documents or try rephrasing your question."
            )

        # Assemble grounded context with strict structural tags
        context_blocks = []
        for c in context_chunks:
            doc_name = c.get("filename", "Unknown Document")
            page_num = c.get("page_number", 1)
            content = c.get("content", "")
            context_blocks.append(
                f"[Source Document: {doc_name} | Page: {page_num}]\n{content}"
            )
        formatted_context = "\n\n---\n\n".join(context_blocks)

        system_prompt = (
            "You are an Enterprise AI Document Assistant designed for precise, context-grounded question answering.\n\n"
            "CRITICAL OPERATING RULES:\n"
            "1. Answer the user's question STRICTLY and ONLY using the provided Document Context below.\n"
            "2. Do NOT extrapolate, speculate, or introduce external knowledge not explicitly supported by the context.\n"
            "3. If the provided context does NOT contain enough information to answer the question with certainty, "
            "explicitly state: 'Based on the provided documents, I could not find information regarding [topic].'\n"
            "4. For EVERY statement, fact, statistic, or claim you make, you MUST cite the exact source document name and page number "
            "inline in the format: [DocumentName, Page X].\n"
            "5. Maintain a professional, executive tone."
        )

        user_content = f"### DOCUMENT CONTEXT:\n{formatted_context}\n\n### USER QUESTION:\n{query}"

        # If client is not configured (e.g. during local tests without API key), provide an informative grounded simulation
        if not self.client:
            logger.warning("OpenAI API key not configured. Returning simulated grounded response.")
            top_doc = context_chunks[0]
            return (
                f"Based on the provided documents, here is the relevant information found: "
                f"\"{top_doc.get('content', '')[:250]}...\" "
                f"[{top_doc.get('filename', 'Doc')}, Page {top_doc.get('page_number', 1)}].\n\n"
                f"(Note: To receive full synthesis from GPT-4o, configure OPENAI_API_KEY in backend/.env)"
            )

        messages = [{"role": "system", "content": system_prompt}]
        
        # Add conversation history if provided (last 4 turns)
        if conversation_history:
            for turn in conversation_history[-4:]:
                messages.append(turn)

        messages.append({"role": "user", "content": user_content})

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"OpenAI API invocation failed: {e}")
            raise
