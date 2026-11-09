import re
from dataclasses import dataclass, field
from typing import List, Dict, Any
from app.services.document_parser import ParsedDocument


@dataclass
class TextChunk:
    chunk_index: int
    page_number: int
    content: str
    token_count: int
    metadata: Dict[str, Any] = field(default_factory=dict)


class TextChunker:
    """
    Page-aware recursive chunker engineered for enterprise documents.
    Splits text while respecting paragraph boundaries, sentences, and 
    preserving precise 1-based page numbers for citation fidelity.
    """

    def __init__(self, chunk_size: int = 800, chunk_overlap: int = 150):
        if chunk_overlap >= chunk_size:
            raise ValueError("chunk_overlap must be strictly less than chunk_size.")
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separators = ["\n\n", "\n", ". ", "? ", "! ", "; ", ", ", " "]

    def _split_text_recursively(self, text: str, separators: List[str]) -> List[str]:
        """Recursively splits a block of text into chunks below chunk_size."""
        text = text.strip()
        if len(text) <= self.chunk_size:
            return [text] if text else []

        # Find first matching separator
        chosen_sep = ""
        remaining_seps: List[str] = []
        for i, sep in enumerate(separators):
            if sep in text:
                chosen_sep = sep
                remaining_seps = separators[i + 1:]
                break

        if not chosen_sep:
            # Fallback hard slice if no separator matches
            chunks = []
            start = 0
            while start < len(text):
                end = min(start + self.chunk_size, len(text))
                chunks.append(text[start:end])
                start += self.chunk_size - self.chunk_overlap
            return chunks

        # Split on the chosen separator
        splits = text.split(chosen_sep)
        good_splits: List[str] = []
        current_chunk: List[str] = []
        current_len = 0

        for s in splits:
            s_clean = s.strip()
            if not s_clean:
                continue

            if len(s_clean) > self.chunk_size and remaining_seps:
                # Recursively split large sub-chunk
                sub_chunks = self._split_text_recursively(s_clean, remaining_seps)
                for sc in sub_chunks:
                    good_splits.append(sc)
            else:
                additional_len = len(s_clean) + len(chosen_sep)
                if current_len + additional_len > self.chunk_size and current_chunk:
                    merged = chosen_sep.join(current_chunk).strip()
                    if merged:
                        good_splits.append(merged)
                    # Overlap handling
                    overlap_chars = 0
                    overlap_chunk = []
                    for item in reversed(current_chunk):
                        if overlap_chars + len(item) < self.chunk_overlap:
                            overlap_chunk.insert(0, item)
                            overlap_chars += len(item) + len(chosen_sep)
                        else:
                            break
                    current_chunk = overlap_chunk + [s_clean]
                    current_len = sum(len(x) + len(chosen_sep) for x in current_chunk)
                else:
                    current_chunk.append(s_clean)
                    current_len += additional_len

        if current_chunk:
            merged = chosen_sep.join(current_chunk).strip()
            if merged:
                good_splits.append(merged)

        return good_splits

    def chunk_document(self, parsed_doc: ParsedDocument, document_id: str) -> List[TextChunk]:
        """
        Chunks the parsed document page by page to ensure every chunk 
        strictly belongs to a known page number without ambiguity.
        """
        chunks: List[TextChunk] = []
        global_index = 0

        for page in parsed_doc.pages:
            page_text = page.text.strip()
            if not page_text:
                continue

            # Split within page
            page_chunks = self._split_text_recursively(page_text, self.separators)

            for raw_chunk in page_chunks:
                chunk_clean = raw_chunk.strip()
                if not chunk_clean or len(chunk_clean) < 15:
                    # Skip trivial whitespace or noise
                    continue

                # Estimate token count (~4 characters per token)
                estimated_tokens = max(1, len(chunk_clean) // 4)

                metadata = {
                    "document_id": document_id,
                    "filename": parsed_doc.filename,
                    "file_type": parsed_doc.file_type,
                    "page_number": page.page_number,
                    "chunk_index": global_index,
                }

                chunks.append(TextChunk(
                    chunk_index=global_index,
                    page_number=page.page_number,
                    content=chunk_clean,
                    token_count=estimated_tokens,
                    metadata=metadata,
                ))
                global_index += 1

        return chunks
