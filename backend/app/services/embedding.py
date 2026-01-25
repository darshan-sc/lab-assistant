import json
import tiktoken
from openai import OpenAI

from app.core.config import settings

EMBEDDING_MODEL = "text-embedding-3-small"
CHUNK_SIZE = 1000  # characters per chunk (legacy)
CHUNK_OVERLAP = 200  # overlap between chunks (legacy)

# Token-based chunking parameters
CHUNK_SIZE_TOKENS = 400  # Target 300-500 tokens per chunk
CHUNK_OVERLAP_TOKENS = 50  # Token overlap between chunks


def get_embeddings(texts: list[str]) -> list[list[float]]:
    """Get embeddings for a list of texts using OpenAI.

    Args:
        texts: List of text strings to embed

    Returns:
        List of embedding vectors (1536 dimensions each)
    """
    client = OpenAI(api_key=settings.OPENAI_API_KEY)

    response = client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=texts,
    )

    return [item.embedding for item in response.data]


def get_embedding(text: str) -> list[float]:
    """Get embedding for a single text."""
    return get_embeddings([text])[0]


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """Split text into overlapping chunks.

    Args:
        text: The text to chunk
        chunk_size: Maximum characters per chunk
        overlap: Number of overlapping characters between chunks

    Returns:
        List of text chunks
    """
    if len(text) <= chunk_size:
        return [text]

    chunks = []
    start = 0

    while start < len(text):
        end = start + chunk_size

        # Try to break at a sentence or paragraph boundary
        if end < len(text):
            # Look for paragraph break first
            para_break = text.rfind('\n\n', start, end)
            if para_break > start + chunk_size // 2:
                end = para_break + 2
            else:
                # Look for sentence break
                sentence_break = max(
                    text.rfind('. ', start, end),
                    text.rfind('? ', start, end),
                    text.rfind('! ', start, end),
                )
                if sentence_break > start + chunk_size // 2:
                    end = sentence_break + 2

        chunks.append(text[start:end].strip())

        # Move start position, accounting for overlap
        start = end - overlap
        if start >= len(text):
            break

    return [c for c in chunks if c]  # Filter empty chunks


def parse_document_sections(text: str) -> list[dict]:
    """Use LLM to identify sections in an academic paper.

    Args:
        text: The full document text

    Returns:
        List of dicts with section info:
        [{"title": "Abstract", "start": 0, "end": 500},
         {"title": "Introduction", "start": 500, "end": 2000}, ...]
    """
    client = OpenAI(api_key=settings.OPENAI_API_KEY)

    # Use first ~12000 chars to identify structure (enough for most papers)
    sample_text = text[:12000] if len(text) > 12000 else text

    system_prompt = """You are a document structure analyzer. Given text from an academic paper,
identify the major sections and their approximate character positions.

Return a JSON array with objects containing:
- "title": The section name (e.g., "Abstract", "Introduction", "Methods", "Results", "Discussion", "Conclusion", "References")
- "start": Approximate character position where section starts
- "end": Approximate character position where section ends

Only include sections that clearly exist in the document. Be precise about character positions.
Return ONLY valid JSON array, no other text."""

    response = client.chat.completions.create(
        model=settings.OPENAI_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Identify sections in this academic paper text:\n\n{sample_text}"},
        ],
        temperature=0,
    )

    try:
        sections = json.loads(response.choices[0].message.content)
        # Validate and clean up sections
        cleaned = []
        for s in sections:
            if isinstance(s, dict) and "title" in s and "start" in s:
                cleaned.append({
                    "title": str(s.get("title", "Unknown")),
                    "start": int(s.get("start", 0)),
                    "end": int(s.get("end", len(text))),
                })
        return cleaned if cleaned else [{"title": "Document", "start": 0, "end": len(text)}]
    except (json.JSONDecodeError, TypeError, ValueError):
        # Fallback: treat entire document as one section
        return [{"title": "Document", "start": 0, "end": len(text)}]


def map_char_to_page(char_offset: int, pages: list[dict]) -> int:
    """Map a character offset to a page number.

    Args:
        char_offset: Character position in the full document text
        pages: List of page dicts from extract_pages_from_pdf()

    Returns:
        Page number (1-indexed) containing this character offset
    """
    for i, page in enumerate(pages):
        page_end = page["char_start"] + len(page["text"])
        if char_offset < page_end:
            return page["page"]
    # Default to last page if offset is beyond document
    return pages[-1]["page"] if pages else 1


def get_section_for_position(char_pos: int, sections: list[dict]) -> str | None:
    """Get section title for a character position.

    Args:
        char_pos: Character position in document
        sections: List of section dicts from parse_document_sections()

    Returns:
        Section title or None if not in a section
    """
    for section in sections:
        if section["start"] <= char_pos < section["end"]:
            return section["title"]
    return None


def chunk_text_by_tokens(
    text: str,
    sections: list[dict] | None = None,
    chunk_size: int = CHUNK_SIZE_TOKENS,
    overlap: int = CHUNK_OVERLAP_TOKENS,
) -> list[dict]:
    """Chunk text by token count, respecting section boundaries.

    Args:
        text: The text to chunk
        sections: Optional list of section dicts from parse_document_sections()
        chunk_size: Target tokens per chunk
        overlap: Token overlap between chunks

    Returns:
        List of chunk dicts:
        [{"content": str, "section_title": str | None, "char_start": int, "char_end": int}, ...]
    """
    # Use cl100k_base encoding (used by GPT-4, text-embedding-3)
    enc = tiktoken.get_encoding("cl100k_base")

    if not sections:
        sections = [{"title": None, "start": 0, "end": len(text)}]

    chunks = []

    for section in sections:
        section_text = text[section["start"]:section["end"]]
        section_start = section["start"]

        if not section_text.strip():
            continue

        tokens = enc.encode(section_text)

        if len(tokens) <= chunk_size:
            # Section fits in one chunk
            chunks.append({
                "content": section_text.strip(),
                "section_title": section.get("title"),
                "char_start": section_start,
                "char_end": section["end"],
            })
            continue

        # Split section into multiple chunks
        token_start = 0
        while token_start < len(tokens):
            token_end = min(token_start + chunk_size, len(tokens))

            # Try to break at sentence boundary
            chunk_tokens = tokens[token_start:token_end]
            chunk_text = enc.decode(chunk_tokens)

            # Find better break point at sentence boundary
            if token_end < len(tokens):
                # Look for sentence endings
                for sep in ['. ', '? ', '! ', '\n\n', '\n']:
                    last_sep = chunk_text.rfind(sep)
                    if last_sep > len(chunk_text) // 2:
                        chunk_text = chunk_text[:last_sep + len(sep)]
                        break

            chunk_text = chunk_text.strip()
            if chunk_text:
                # Calculate character offsets
                char_start_in_section = len(enc.decode(tokens[:token_start]))
                char_end_in_section = char_start_in_section + len(chunk_text)

                chunks.append({
                    "content": chunk_text,
                    "section_title": section.get("title"),
                    "char_start": section_start + char_start_in_section,
                    "char_end": section_start + char_end_in_section,
                })

            # Move forward with overlap
            actual_chunk_tokens = len(enc.encode(chunk_text))
            token_start += max(actual_chunk_tokens - overlap, 1)

    return chunks
