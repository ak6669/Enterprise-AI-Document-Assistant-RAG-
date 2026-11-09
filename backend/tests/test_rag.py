from unittest.mock import MagicMock
from app.services.rag_service import RAGService
from app.schemas.chat import Citation


def test_rag_citation_extraction():
    mock_embedding = MagicMock()
    mock_vector_store = MagicMock()
    mock_llm = MagicMock()

    rag = RAGService(
        embedding_service=mock_embedding,
        vector_store=mock_vector_store,
        llm_service=mock_llm
    )

    chunks = [
        {
            "chunk_id": "doc1_chunk_0",
            "content": "Azure Container Apps is a serverless platform.",
            "document_id": "doc-azure",
            "filename": "azure_guide.pdf",
            "page_number": 4,
            "chunk_index": 0,
            "similarity_score": 0.89,
        },
        {
            "chunk_id": "doc2_chunk_1",
            "content": "PostgreSQL is used for relational metadata storage.",
            "document_id": "doc-pg",
            "filename": "db_architecture.docx",
            "page_number": 2,
            "chunk_index": 1,
            "similarity_score": 0.81,
        }
    ]

    answer = "Azure Container Apps is serverless [azure_guide.pdf, Page 4]."
    citations = rag._extract_citations(answer, chunks)

    assert len(citations) == 2
    
    first_citation = citations[0]
    assert isinstance(first_citation, Citation)
    assert first_citation.filename == "azure_guide.pdf"
    assert first_citation.page_number == 4
    assert first_citation.document_id == "doc-azure"
    assert "Azure Container Apps is a serverless" in first_citation.excerpt
    assert first_citation.score == 0.89

    second_citation = citations[1]
    assert isinstance(second_citation, Citation)
    assert second_citation.filename == "db_architecture.docx"
    assert second_citation.page_number == 2
    assert first_citation.chunk_id == "doc1_chunk_0"
