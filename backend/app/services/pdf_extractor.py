import fitz  # PyMuPDF


def extract_pages_from_pdf(pdf_path: str) -> list[dict]:
    """Extract text with page numbers from a PDF file.

    Args:
        pdf_path: Path to the PDF file

    Returns:
        List of dicts with {"page": int (1-indexed), "text": str, "char_start": int}
        where char_start is the character offset where this page starts in the full text

    Raises:
        Exception: If PDF cannot be opened or read
    """
    doc = fitz.open(pdf_path)
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


def extract_text_from_pdf(pdf_path: str) -> str:
    """Extract all text content from a PDF file.

    Args:
        pdf_path: Path to the PDF file

    Returns:
        Full text content of the PDF

    Raises:
        Exception: If PDF cannot be opened or read
    """
    doc = fitz.open(pdf_path)
    text_parts = []

    for page in doc:
        text_parts.append(page.get_text())

    doc.close()
    full_text = "\n".join(text_parts)
    # Remove NUL characters that PostgreSQL doesn't allow in text fields
    return full_text.replace('\x00', '')


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
