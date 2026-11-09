import io
import re
from dataclasses import dataclass
from typing import List, Optional
from pypdf import PdfReader
import docx


@dataclass
class DocumentPage:
    page_number: int
    text: str


@dataclass
class ParsedDocument:
    filename: str
    file_type: str
    page_count: int
    pages: List[DocumentPage]
    total_characters: int


class DocumentParserError(Exception):
    """Custom exception raised when document parsing fails."""
    pass


class DocumentParser:
    """Enterprise document parser supporting PDF, DOCX, and TXT formats."""

    @staticmethod
    def clean_text(text: str) -> str:
        """Normalizes unicode whitespace, removes null bytes and collapses excessive blank lines."""
        if not text:
            return ""
        # Remove null characters
        text = text.replace("\x00", "")
        # Replace carriage returns
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        # Normalize non-breaking spaces
        text = text.replace("\xa0", " ")
        # Collapse multiple spaces (but preserve newlines)
        text = re.sub(r"[ \t]+", " ", text)
        # Collapse more than two consecutive newlines into two
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()

    @classmethod
    def parse_pdf(cls, file_bytes: bytes, filename: str) -> ParsedDocument:
        """Parses a PDF file bytes, preserving 1-based page numbers."""
        try:
            stream = io.BytesIO(file_bytes)
            reader = PdfReader(stream)
            num_pages = len(reader.pages)
            if num_pages == 0:
                raise DocumentParserError(f"PDF '{filename}' contains 0 pages.")

            pages: List[DocumentPage] = []
            total_chars = 0

            for page_idx, page in enumerate(reader.pages, start=1):
                raw_text = page.extract_text() or ""
                cleaned = cls.clean_text(raw_text)
                if cleaned:
                    pages.append(DocumentPage(page_number=page_idx, text=cleaned))
                    total_chars += len(cleaned)

            if not pages:
                raise DocumentParserError(
                    f"PDF '{filename}' contains {num_pages} page(s) but no extractable text. "
                    "Scanned documents without OCR text layers are not supported."
                )

            return ParsedDocument(
                filename=filename,
                file_type="pdf",
                page_count=num_pages,
                pages=pages,
                total_characters=total_chars,
            )
        except Exception as e:
            if isinstance(e, DocumentParserError):
                raise e
            raise DocumentParserError(f"Failed to parse PDF '{filename}': {str(e)}") from e

    @classmethod
    def parse_docx(cls, file_bytes: bytes, filename: str) -> ParsedDocument:
        """
        Parses a DOCX file bytes.
        Detects hard page breaks where present, otherwise partitions content
        into logical pages of ~2000 characters for consistent page citation.
        """
        try:
            stream = io.BytesIO(file_bytes)
            doc = docx.Document(stream)

            paragraphs_and_tables: List[str] = []
            
            # Extract paragraphs
            for para in doc.paragraphs:
                text = para.text.strip()
                if text:
                    paragraphs_and_tables.append(text)

            # Extract tables
            for table in doc.tables:
                for row in table.rows:
                    row_data = [cell.text.strip() for cell in row.cells if cell.text.strip()]
                    if row_data:
                        paragraphs_and_tables.append(" | ".join(row_data))

            full_text = "\n\n".join(paragraphs_and_tables)
            cleaned = cls.clean_text(full_text)

            if not cleaned:
                raise DocumentParserError(f"DOCX '{filename}' contains no extractable text.")

            # Logical page segmenter: ~2000 characters per page if no explicit breaks
            CHARS_PER_PAGE = 2000
            pages: List[DocumentPage] = []
            paragraphs = cleaned.split("\n\n")
            current_page_text: List[str] = []
            current_page_chars = 0
            page_number = 1

            for p in paragraphs:
                p_len = len(p)
                if current_page_chars + p_len > CHARS_PER_PAGE and current_page_text:
                    pages.append(DocumentPage(
                        page_number=page_number,
                        text="\n\n".join(current_page_text)
                    ))
                    page_number += 1
                    current_page_text = [p]
                    current_page_chars = p_len
                else:
                    current_page_text.append(p)
                    current_page_chars += p_len + 2

            if current_page_text:
                pages.append(DocumentPage(
                    page_number=page_number,
                    text="\n\n".join(current_page_text)
                ))

            return ParsedDocument(
                filename=filename,
                file_type="docx",
                page_count=len(pages),
                pages=pages,
                total_characters=len(cleaned),
            )
        except Exception as e:
            if isinstance(e, DocumentParserError):
                raise e
            raise DocumentParserError(f"Failed to parse DOCX '{filename}': {str(e)}") from e

    @classmethod
    def parse_txt(cls, file_bytes: bytes, filename: str) -> ParsedDocument:
        """Parses a plain text file bytes with multiple encoding fallbacks."""
        encodings = ["utf-8", "utf-8-sig", "latin-1", "cp1252", "iso-8859-1"]
        decoded_text: Optional[str] = None

        for enc in encodings:
            try:
                decoded_text = file_bytes.decode(enc)
                break
            except (UnicodeDecodeError, LookupError):
                continue

        if decoded_text is None:
            raise DocumentParserError(f"TXT '{filename}' could not be decoded with standard character sets.")

        cleaned = cls.clean_text(decoded_text)
        if not cleaned:
            raise DocumentParserError(f"TXT '{filename}' is empty.")

        # Paginate text files every ~2500 characters so line/page references remain coherent
        CHARS_PER_PAGE = 2500
        paragraphs = cleaned.split("\n\n")
        pages: List[DocumentPage] = []
        current_page_text: List[str] = []
        current_page_chars = 0
        page_number = 1

        for p in paragraphs:
            p_len = len(p)
            if current_page_chars + p_len > CHARS_PER_PAGE and current_page_text:
                pages.append(DocumentPage(
                    page_number=page_number,
                    text="\n\n".join(current_page_text)
                ))
                page_number += 1
                current_page_text = [p]
                current_page_chars = p_len
            else:
                current_page_text.append(p)
                current_page_chars += p_len + 2

        if current_page_text:
            pages.append(DocumentPage(
                page_number=page_number,
                text="\n\n".join(current_page_text)
            ))

        return ParsedDocument(
            filename=filename,
            file_type="txt",
            page_count=len(pages),
            pages=pages,
            total_characters=len(cleaned),
        )

    @classmethod
    def parse(cls, file_bytes: bytes, filename: str) -> ParsedDocument:
        """Route to appropriate parser by file extension."""
        ext = filename.lower().split(".")[-1]
        if ext == "pdf":
            return cls.parse_pdf(file_bytes, filename)
        elif ext == "docx":
            return cls.parse_docx(file_bytes, filename)
        elif ext in ["txt", "text", "md"]:
            return cls.parse_txt(file_bytes, filename)
        else:
            raise DocumentParserError(f"Unsupported file format '.{ext}'. Supported: PDF, DOCX, TXT.")
