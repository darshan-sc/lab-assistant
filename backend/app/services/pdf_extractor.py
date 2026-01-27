import asyncio
import fitz  # PyMuPDF


def _extract_pages_from_bytes_sync(pdf_bytes: bytes) -> list[dict]:
    """Synchronous implementation of PDF page extraction from bytes."""
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    pages = []
    char_offset = 0

    for page_num, page in enumerate(doc, start=1):
        text = page.get_text()
        # Remove NUL characters that PostgreSQL doesn't allow
        text = text.replace('\x00', '')
        pages.append({
            "page": page_num,
            "text": text,
            "char_start": char_offset,
        })
        # Add 1 for the newline that joins pages
        char_offset += len(text) + 1

    doc.close()
    return pages


async def extract_pages_from_bytes(pdf_bytes: bytes) -> list[dict]:
    """Extract text with page numbers from PDF bytes.

    Args:
        pdf_bytes: PDF file content as bytes

    Returns:
        List of dicts with {"page": int (1-indexed), "text": str, "char_start": int}
        where char_start is the character offset where this page starts in the full text

    Raises:
        Exception: If PDF cannot be opened or read
    """
    return await asyncio.to_thread(_extract_pages_from_bytes_sync, pdf_bytes)


def _extract_text_from_bytes_sync(pdf_bytes: bytes) -> str:
    """Synchronous implementation of PDF text extraction from bytes."""
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    text_parts = []

    for page in doc:
        text_parts.append(page.get_text())

    doc.close()
    full_text = "\n".join(text_parts)
    # Remove NUL characters that PostgreSQL doesn't allow in text fields
    return full_text.replace('\x00', '')


async def extract_text_from_bytes(pdf_bytes: bytes) -> str:
    """Extract all text content from PDF bytes.

    Args:
        pdf_bytes: PDF file content as bytes

    Returns:
        Full text content of the PDF

    Raises:
        Exception: If PDF cannot be opened or read
    """
    return await asyncio.to_thread(_extract_text_from_bytes_sync, pdf_bytes)


def get_first_n_chars(text: str, n: int = 8000) -> str:
    """Truncate text to first n characters for LLM context.

    Args:
        text: The text to truncate
        n: Maximum number of characters

    Returns:
        Truncated text
    """
    if len(text) <= n:
        return text
    return text[:n]
