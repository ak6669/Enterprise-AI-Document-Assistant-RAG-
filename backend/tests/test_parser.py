import io
import pytest
from pypdf import PdfWriter
import docx

from app.services.document_parser import DocumentParser, DocumentParserError, ParsedDocument


def create_sample_pdf_bytes(pages_text: list[str]) -> bytes:
    """Helper to generate an in-memory PDF for unit testing."""
    # Using reportlab or basic pypdf writer
    # pypdf Writer can create a valid blank page and annotate or we can use basic PDF stream
    # Instead of external reportlab, let's test pypdf with standard pdf header or mock
    # A minimal valid multi-page PDF can be constructed using reportlab if available or pypdf
    pass


class TestDocumentParser:

    def test_clean_text(self):
        raw = "Hello   world!\r\n\r\n\r\n\r\nThis is\xa0a test.\x00"
        cleaned = DocumentParser.clean_text(raw)
        assert "Hello world!" in cleaned
        assert "\xa0" not in cleaned
        assert "\x00" not in cleaned
        assert "\n\n\n" not in cleaned

    def test_parse_txt_single_page(self):
        sample_txt = b"Enterprise AI Document Assistant.\nPage 1 text content."
        parsed = DocumentParser.parse_txt(sample_txt, "sample.txt")
        assert isinstance(parsed, ParsedDocument)
        assert parsed.filename == "sample.txt"
        assert parsed.file_type == "txt"
        assert parsed.page_count == 1
        assert len(parsed.pages) == 1
        assert parsed.pages[0].page_number == 1
        assert "Enterprise AI Document Assistant" in parsed.pages[0].text

    def test_parse_txt_multi_page(self):
        # Generate text > 2500 chars to verify pagination
        paragraphs = ["Paragraph " + str(i) + ": " + ("Data " * 80) for i in range(10)]
        sample_txt = "\n\n".join(paragraphs).encode("utf-8")
        parsed = DocumentParser.parse_txt(sample_txt, "large.txt")
        assert parsed.page_count > 1
        assert parsed.pages[0].page_number == 1
        assert parsed.pages[1].page_number == 2

    def test_parse_empty_txt_raises(self):
        with pytest.raises(DocumentParserError):
            DocumentParser.parse_txt(b"    \n   ", "empty.txt")

    def test_parse_docx(self):
        # Create an in-memory DOCX
        doc = docx.Document()
        doc.add_heading("Enterprise RAG Specification", level=1)
        doc.add_paragraph("This is the main introduction to the enterprise system.")
        table = doc.add_table(rows=2, cols=2)
        table.rows[0].cells[0].text = "Header 1"
        table.rows[0].cells[1].text = "Header 2"
        table.rows[1].cells[0].text = "Value A"
        table.rows[1].cells[1].text = "Value B"

        stream = io.BytesIO()
        doc.save(stream)
        docx_bytes = stream.getvalue()

        parsed = DocumentParser.parse_docx(docx_bytes, "test.docx")
        assert parsed.filename == "test.docx"
        assert parsed.file_type == "docx"
        assert parsed.page_count >= 1
        assert "Enterprise RAG Specification" in parsed.pages[0].text
        assert "Header 1 | Header 2" in parsed.pages[0].text

    def test_unsupported_file_extension(self):
        with pytest.raises(DocumentParserError, match="Unsupported file format"):
            DocumentParser.parse(b"dummy data", "image.png")
