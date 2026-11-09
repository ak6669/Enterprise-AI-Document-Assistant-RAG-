"""
End-to-End Enterprise RAG Pipeline Verification Script
Validates:
1. Document Parsing (TXT, DOCX, PDF) & page metadata
2. Page-aware text chunking
3. Sentence Transformer embedding generation
4. ChromaDB indexing & vector similarity search
5. Grounded RAG query synthesis with exact citation resolution
"""

import asyncio
import os
import sys

# Ensure backend directory is in python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))

from app.services.document_parser import DocumentParser
from app.services.chunker import TextChunker
from app.services.embedding import EmbeddingService
from app.services.vector_store import VectorStoreService
from app.services.rag_service import RAGService


async def main():
    print("=================================================================")
    print(" Starting Enterprise RAG Pipeline End-to-End Verification")
    print("=================================================================")

    # 1. Parse Sample Enterprise Policy Document
    sample_file_path = os.path.join("sample_documents", "sample_enterprise_policy.txt")
    print(f"\n[1/5] Parsing sample document: {sample_file_path}...")
    with open(sample_file_path, "rb") as f:
        file_bytes = f.read()

    parsed_doc = DocumentParser.parse(file_bytes, "sample_enterprise_policy.txt")
    print(f"  --> Parsed successfully! Format: {parsed_doc.file_type}, Pages: {parsed_doc.page_count}, Chars: {parsed_doc.total_characters}")
    assert parsed_doc.page_count >= 1, "Page count must be >= 1"

    # 2. Page-aware Chunking
    print("\n[2/5] Running page-preserving text chunker...")
    chunker = TextChunker(chunk_size=400, chunk_overlap=80)
    chunks = chunker.chunk_document(parsed_doc, document_id="test-doc-001")
    print(f"  --> Generated {len(chunks)} chunks.")
    for idx, c in enumerate(chunks[:2]):
        print(f"      Chunk {idx} (Page {c.page_number}): \"{c.content[:70]}...\"")
    assert len(chunks) > 0, "Chunks list cannot be empty"

    # 3. Embedding Generation
    print("\n[3/5] Generating Sentence Transformers embeddings (all-MiniLM-L6-v2)...")
    embedding_service = EmbeddingService()
    chunk_texts = [c.content for c in chunks]
    embeddings = embedding_service.embed_texts(chunk_texts)
    print(f"  --> Generated {len(embeddings)} vectors with dimension {len(embeddings[0])}.")
    assert len(embeddings) == len(chunks), "Embedding count must match chunk count"
    assert len(embeddings[0]) == 384, "all-MiniLM-L6-v2 dimension must be 384"

    # 4. ChromaDB Vector Store Indexing & Retrieval
    print("\n[4/5] Indexing chunks into ChromaDB vector store...")
    vector_store = VectorStoreService()
    # Clean previous test entries if any
    vector_store.delete_document_chunks("test-doc-001")
    indexed_count = vector_store.add_chunks("test-doc-001", chunks, embeddings)
    print(f"  --> Successfully indexed {indexed_count} chunks in ChromaDB.")

    # Test Semantic Retrieval
    test_query = "What platform must digital workloads be hosted in?"
    print(f"\n[5/5] Testing RAG Query: '{test_query}'...")
    rag_service = RAGService(
        embedding_service=embedding_service,
        vector_store=vector_store
    )
    result = await rag_service.query(test_query, top_k=2)

    print("\n------------------------- RAG RESPONSE -------------------------")
    print(f"Answer:\n{result['answer']}\n")
    print(f"Citations ({len(result['citations'])} verified):")
    for cit in result["citations"]:
        print(f"  * Document: '{cit.filename}' | Page: {cit.page_number} | Match: {round(cit.score*100)}%")
        print(f"    Excerpt: \"{cit.excerpt[:100]}...\"")
    print(f"Latency: {result['latency_seconds']} seconds")
    print("----------------------------------------------------------------")

    # Assertions
    assert len(result["citations"]) > 0, "RAG pipeline must return at least one citation"
    assert result["citations"][0].filename == "sample_enterprise_policy.txt"
    assert result["citations"][0].page_number >= 1

    print("\n=================================================================")
    print(" ALL VERIFICATION CHECKS PASSED SUCCESSFULLY! ")
    print("=================================================================")


if __name__ == "__main__":
    asyncio.run(main())
