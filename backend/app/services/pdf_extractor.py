import fitz  # PyMuPDF


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
    return "\n".join(text_parts)


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
