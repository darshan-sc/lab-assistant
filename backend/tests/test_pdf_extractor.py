"""
Test PDF extraction utilities.

Difficulty: 2/7
Pure functions — no database or network calls needed.
You'll need a small sample PDF for the extraction tests; see the helper below.

Run just this file:
    pytest tests/test_pdf_extractor.py

Tip: You can create a tiny PDF in-memory with the `fpdf2` package, or just
     test `get_first_n_chars` which only needs a plain string.
"""

import pytest

from app.services.pdf_extractor import (
    get_first_n_chars,
    _extract_text_from_bytes_sync,
    _extract_pages_from_bytes_sync,
)


# ---------------------------------------------------------------------------
# Helper: create a minimal PDF in memory (requires PyMuPDF / fitz)
# ---------------------------------------------------------------------------
def _make_sample_pdf(pages: list[str]) -> bytes:
    """Create a PDF with the given page texts and return its bytes.

    Uses PyMuPDF (fitz) which is already a project dependency.
    Each string in `pages` becomes one page.

    Example:
        pdf_bytes = _make_sample_pdf(["Hello page 1", "Hello page 2"])
    """
    import fitz  # PyMuPDF

    doc = fitz.open()
    for text in pages:
        page = doc.new_page()
        page.insert_text((72, 72), text)
    data = doc.tobytes()
    doc.close()
    return data


# ---------------------------------------------------------------------------
# Tests for get_first_n_chars  (no PDF needed)
# ---------------------------------------------------------------------------

class TestGetFirstNChars:
    """Test the simple text-truncation helper."""

    def test_short_text_unchanged(self):
        """Text shorter than n should be returned as-is."""
        # Example (filled in):
        result = get_first_n_chars("hello", n=100)
        assert result == "hello"

    def test_truncates_at_n(self):
        # TODO: Pass a 100-char string with n=50, verify len(result) == 50
        pass

    def test_default_n(self):
        # TODO: Verify the default n=8000 works (pass a 10_000-char string)
        pass

    def test_empty_string(self):
        # TODO: get_first_n_chars("") should return ""
        pass


# ---------------------------------------------------------------------------
# Tests for _extract_text_from_bytes_sync
# ---------------------------------------------------------------------------

class TestExtractTextFromBytes:
    """Test full-text extraction from PDF bytes."""

    def test_single_page_pdf(self):
        # TODO: Use _make_sample_pdf(["Hello world"]) and verify
        #       _extract_text_from_bytes_sync returns text containing "Hello world"
        pass

    def test_multi_page_pdf(self):
        # TODO: Two-page PDF; verify both pages' text appears in output
        pass

    def test_empty_pdf(self):
        # TODO: PDF with a single blank page — should return empty string
        pass

    def test_invalid_bytes_raises(self):
        # TODO: Passing b"not a pdf" should raise an exception
        pass


# ---------------------------------------------------------------------------
# Tests for _extract_pages_from_bytes_sync
# ---------------------------------------------------------------------------

class TestExtractPagesFromBytes:
    """Test page-by-page extraction with char_start offsets."""

    def test_returns_list_of_dicts(self):
        # TODO: Verify result is a list of dicts with keys: page, text, char_start
        pass

    def test_page_numbers_are_1_indexed(self):
        # TODO: First page dict should have page=1
        pass

    def test_char_start_offsets_increase(self):
        # TODO: For a multi-page PDF, char_start of page 2 > char_start of page 1
        pass

    def test_single_page_char_start_is_zero(self):
        # TODO: Single-page PDF should have char_start=0
        pass
