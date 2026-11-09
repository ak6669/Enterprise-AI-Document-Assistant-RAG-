import pytest
from app.services.document_parser import ParsedDocument, DocumentPage
from app.services.chunker import TextChunker, TextChunk


class TestTextChunker:

    def test_chunk_page_preservation(self):
        doc = ParsedDocument(
            filename="financial_report.pdf",
            file_type="pdf",
            page_count=3,
            pages=[
                DocumentPage(page_number=1, text="Page 1: In Q1, revenue grew by 15 percent year-over-year. Operating margin expanded to 22 percent."),
                DocumentPage(page_number=2, text="Page 2: In Q2, international expansion drove cloud adoption. Europe revenue reached 40 million dollars."),
                DocumentPage(page_number=3, text="Page 3: Total FY outlook remains positive. Projected net profit is 120 million dollars."),
            ],
            total_characters=300
        )

        chunker = TextChunker(chunk_size=150, chunk_overlap=30)
        chunks = chunker.chunk_document(doc, document_id="doc-123")

        assert len(chunks) >= 3
        # Ensure every chunk corresponds strictly to its originating page
        pages_in_chunks = [c.page_number for c in chunks]
        assert 1 in pages_in_chunks
        assert 2 in pages_in_chunks
        assert 3 in pages_in_chunks

        # Verify chunk metadata
        for c in chunks:
            assert c.metadata["document_id"] == "doc-123"
            assert c.metadata["filename"] == "financial_report.pdf"
            assert c.metadata["page_number"] == c.page_number
            assert len(c.content) > 0

    def test_chunk_recursive_splitting(self):
        long_paragraph = "Sentence one is clear. " * 30  # ~690 characters
        doc = ParsedDocument(
            filename="policy.txt",
            file_type="txt",
            page_count=1,
            pages=[DocumentPage(page_number=1, text=long_paragraph)],
            total_characters=len(long_paragraph)
        )

        chunker = TextChunker(chunk_size=200, chunk_overlap=40)
        chunks = chunker.chunk_document(doc, document_id="doc-456")

        assert len(chunks) > 1
        for c in chunks:
            # Check chunks are within boundary or respect sentence boundaries
            assert len(c.content) <= 260
            assert c.page_number == 1

    def test_invalid_chunk_overlap_raises(self):
        with pytest.raises(ValueError):
            TextChunker(chunk_size=100, chunk_overlap=120)
