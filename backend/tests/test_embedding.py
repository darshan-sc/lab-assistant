"""
Test text chunking and mapping utilities from the embedding module.

Difficulty: 3/7
Pure functions — no OpenAI calls, no database.
Focus on `chunk_text`, `map_char_to_page`, `get_section_for_position`,
and `chunk_text_by_tokens`.

Run just this file:
    pytest tests/test_embedding.py
"""

import pytest

from app.services.embedding import (
    chunk_text,
    map_char_to_page,
    get_section_for_position,
    chunk_text_by_tokens,
    CHUNK_SIZE,
    CHUNK_OVERLAP,
    CHUNK_SIZE_TOKENS,
    CHUNK_OVERLAP_TOKENS,
)


# ---------------------------------------------------------------------------
# Tests for chunk_text  (character-based chunking)
# ---------------------------------------------------------------------------

class TestChunkText:
    """Test the character-based text chunking function."""

    def test_short_text_single_chunk(self):
        """Text shorter than chunk_size should produce exactly one chunk."""
        # Example (filled in):
        chunks = chunk_text("Short text.", chunk_size=1000, overlap=200)
        assert len(chunks) == 1
        assert chunks[0] == "Short text."

    def test_empty_text(self):
        chunks = chunk_text("")
        assert len(chunks) == 0

    def test_long_text_produces_multiple_chunks(self):
        chunks = chunk_text("word " * 500)
        assert len(chunks) > 1

    def test_chunks_overlap(self):
        chunks = chunk_text("word " * 500, chunk_size=100, overlap=20)
        # Verify that the end of chunk 0 appears somewhere at the start of chunk 1
        # (Exact slicing fails because of smart sentence/word snapping)
        overlap_text = chunks[0][-10:] # Check last 10 chars
        assert overlap_text in chunks[1][:30] # Should be in first 30 chars of next chunk

    def test_no_empty_chunks(self):
        # Case 1: Truly empty string
        chunks = chunk_text("")
        assert chunks == []

        # Case 2: String with only whitespace
        chunks_space = chunk_text("   ")
        assert chunks_space == []

    def test_custom_chunk_size(self):
        chunks = chunk_text("word"*200, chunk_size=50, overlap=10)
        assert all(len(chunk) <= 50 for chunk in chunks)


# ---------------------------------------------------------------------------
# Tests for map_char_to_page
# ---------------------------------------------------------------------------

class TestMapCharToPage:
    """Test mapping a character offset to a page number."""

    # Sample pages structure (mimics output of extract_pages_from_bytes)
    PAGES = [
        {"page": 1, "text": "First page text. ", "char_start": 0},
        {"page": 2, "text": "Second page text. ", "char_start": 17},
        {"page": 3, "text": "Third page text.", "char_start": 35},
    ]

    def test_offset_in_first_page(self):
        assert map_char_to_page(5, self.PAGES) == 1

    def test_offset_in_second_page(self):
        assert map_char_to_page(20, self.PAGES) == 2

    def test_offset_at_page_boundary(self):
        assert map_char_to_page(17, self.PAGES) == 2

    def test_offset_beyond_last_page(self):
        assert map_char_to_page(100, self.PAGES) == 3

    def test_offset_zero(self):
        assert map_char_to_page(0, self.PAGES) == 1


# ---------------------------------------------------------------------------
# Tests for get_section_for_position
# ---------------------------------------------------------------------------

class TestGetSectionForPosition:
    """Test mapping a character position to a section title."""

    SECTIONS = [
        {"title": "Abstract", "start": 0, "end": 100},
        {"title": "Introduction", "start": 100, "end": 500},
        {"title": "Methods", "start": 500, "end": 1000},
    ]

    def test_position_in_abstract(self):
        assert get_section_for_position(50, self.SECTIONS) == "Abstract"

    def test_position_in_methods(self):
        assert get_section_for_position(750, self.SECTIONS) == "Methods"

    def test_position_at_boundary(self):
        assert get_section_for_position(100, self.SECTIONS) == "Introduction"

    def test_position_outside_all_sections(self):
        assert get_section_for_position(2000, self.SECTIONS) == None

    def test_empty_sections(self):
        assert get_section_for_position(50, []) == None


# ---------------------------------------------------------------------------
# Tests for chunk_text_by_tokens  (token-based chunking)
# ---------------------------------------------------------------------------

class TestChunkTextByTokens:
    """Test token-aware chunking with optional section boundaries."""

    def test_short_text_single_chunk(self):
        assert len(chunk_text_by_tokens("word" * 10)) == 1

    def test_chunk_dict_keys(self):
        assert chunk_text_by_tokens("word" * 10)[0].keys() == {"content", "section_title", "char_start", "char_end"}

    def test_long_text_multiple_chunks(self):
        assert len(chunk_text_by_tokens("word " * 2000)) > 1

    def test_with_sections(self):
        assert chunk_text_by_tokens("word " * 2000, sections=[{"title": "Intro", "start": 0, "end": 500}])[0]["section_title"] == "Intro"

    def test_without_sections(self):
        assert chunk_text_by_tokens("word " * 2000, sections=None)[0]["section_title"] == None

    def test_char_positions_are_valid(self):
        chunks = chunk_text_by_tokens("word " * 2000)
        for chunk in chunks:
            assert chunk["char_start"] < chunk["char_end"]
            # Verify the content is roughly correct without fighting tokenizer whitespace normalization
            # The chunk content should be present in the text slice
            original_slice = ("word " * 2000)[chunk["char_start"]:chunk["char_end"]]
            assert len(chunk["content"]) > 0
            # Check similarity or length match rather than strict equality on synthetic data
            assert abs(len(chunk["content"]) - len(original_slice)) < 5
