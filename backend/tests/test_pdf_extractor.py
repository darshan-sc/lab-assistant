"""
Test PDF extraction utilities.

Run just this file:
    pytest tests/test_pdf_extractor.py
"""

import pytest

from app.services.pdf_extractor import get_first_n_chars


class TestGetFirstNChars:
    """Test the simple text-truncation helper."""

    def test_short_text_unchanged(self):
        """Text shorter than n should be returned as-is."""
        result = get_first_n_chars("hello", n=100)
        assert result == "hello"
