import json
import re
from sqlalchemy.orm import Session
from sqlalchemy import select, delete
from openai import OpenAI

from app.core.config import settings
from app.models import Paper, Chunk, ChunkSource
from app.services.embedding import (
    get_embeddings,
    get_embedding,
    parse_document_sections,
    chunk_text_by_tokens,
    map_char_to_page,
)
from app.services.pdf_extractor import extract_pages_from_pdf


# Grounded answer system prompt for auditable citations
GROUNDED_SYSTEM_PROMPT = """You are a research assistant. Answer ONLY using the provided context.

CRITICAL RULES:
1. If information is NOT in the context, respond: "This information was not found in the provided documents."
2. Only make claims that are directly supported by the context.
3. Write your answer as clean prose WITHOUT inline citation markers like [1], [2], etc.
4. After your answer, list the exact quotes you used from each numbered source.

Format your response as:
ANSWER: [Your answer as clean prose, no citation markers]

QUOTES USED:
[1]: "exact quote from source 1"
[2]: "exact quote from source 2"
"""


def index_paper(db: Session, paper: Paper) -> int:
    """Index a paper's content into chunks with embeddings and metadata.

    Uses page-aware extraction and structure-aware chunking for better
    citation support.

    Args:
        db: Database session
        paper: Paper to index (must have pdf_path or extracted_text)

    Returns:
        Number of chunks created
    """
    # Delete existing chunks for this paper
    db.execute(
        delete(Chunk).where(
            Chunk.paper_id == paper.id,
            Chunk.source_type == ChunkSource.PAPER.value
        )
    )

    pages = None
    full_text = paper.extracted_text

    # Try to extract with page tracking if PDF is available
    if paper.pdf_path:
        try:
            pages = extract_pages_from_pdf(paper.pdf_path)
            full_text = "\n".join(p["text"] for p in pages)
        except Exception:
            # Fall back to existing extracted_text
            pass

    if not full_text:
        raise ValueError("Paper has no extracted text to index")

    # Parse document structure using LLM
    sections = parse_document_sections(full_text)

    # Chunk text respecting sections and using token limits
    chunk_data = chunk_text_by_tokens(full_text, sections)

    if not chunk_data:
        return 0

    # Get embeddings for all chunks
    contents = [c["content"] for c in chunk_data]
    embeddings = get_embeddings(contents)

    # Extract document metadata from paper
    doc_title = paper.title
    doc_authors = None  # Could be added if Paper model has authors field
    doc_year = None  # Could be added if Paper model has year field

    # Create chunk records with metadata
    for i, (chunk_info, embedding) in enumerate(zip(chunk_data, embeddings)):
        # Map character offsets to page numbers
        page_start = None
        page_end = None
        if pages:
            page_start = map_char_to_page(chunk_info["char_start"], pages)
            page_end = map_char_to_page(chunk_info["char_end"], pages)

        chunk = Chunk(
            user_id=paper.user_id,
            project_id=paper.project_id,
            source_type=ChunkSource.PAPER.value,
            source_id=paper.id,
            paper_id=paper.id,
            content=chunk_info["content"],
            chunk_index=i,
            embedding=embedding,
            # New RAG quality fields
            page_start=page_start,
            page_end=page_end,
            section_title=chunk_info.get("section_title"),
            doc_title=doc_title,
            doc_authors=doc_authors,
            doc_year=doc_year,
        )
        db.add(chunk)

    db.commit()
    return len(chunk_data)


def llm_rerank(query: str, chunks: list[Chunk], top_k: int = 8) -> list[Chunk]:
    """Rerank chunks using LLM to score relevance.

    Args:
        query: The user's query
        chunks: List of candidate chunks from vector search
        top_k: Number of top chunks to return

    Returns:
        Reranked list of top_k most relevant chunks
    """
    if len(chunks) <= top_k:
        return chunks

    client = OpenAI(api_key=settings.OPENAI_API_KEY)

    # Build chunk descriptions for ranking
    chunk_texts = []
    for i, chunk in enumerate(chunks):
        preview = chunk.content[:500] if len(chunk.content) > 500 else chunk.content
        chunk_texts.append(f"[{i}] {preview}")

    chunks_str = "\n\n".join(chunk_texts)

    prompt = f"""Given this query: "{query}"

Rate each text chunk's relevance on a scale of 1-10 (10 = highly relevant, directly answers the query).

Chunks:
{chunks_str}

Return a JSON array of objects with "index" and "score" for each chunk, sorted by score descending.
Example: [{{"index": 2, "score": 9}}, {{"index": 0, "score": 7}}, ...]

Return ONLY the JSON array, no other text."""

    response = client.chat.completions.create(
        model=settings.OPENAI_MODEL,
        messages=[
            {"role": "system", "content": "You are a relevance scoring assistant. Return only valid JSON."},
            {"role": "user", "content": prompt},
        ],
        temperature=0,
    )

    try:
        scores = json.loads(response.choices[0].message.content)
        # Sort by score and get top_k indices
        sorted_scores = sorted(scores, key=lambda x: x.get("score", 0), reverse=True)
        top_indices = [s["index"] for s in sorted_scores[:top_k] if "index" in s]

        # Return chunks in ranked order
        return [chunks[i] for i in top_indices if i < len(chunks)]
    except (json.JSONDecodeError, TypeError, KeyError):
        # Fallback: return first top_k chunks
        return chunks[:top_k]


def retrieve_chunks(
    db: Session,
    user_id: int,
    query: str,
    project_id: int | None = None,
    paper_id: int | None = None,
    experiment_id: int | None = None,
    initial_k: int = 40,
    final_k: int = 8,
    use_reranking: bool = True,
    top_k: int | None = None,  # Deprecated: use final_k instead
) -> list[Chunk]:
    """Retrieve the most relevant chunks using two-stage retrieval.

    Stage 1: Vector search for initial_k candidates
    Stage 2: LLM reranking to select final_k best matches

    Args:
        db: Database session
        user_id: User ID to filter chunks
        query: Query text to search for
        project_id: Optional project ID to filter chunks
        paper_id: Optional paper ID to filter chunks
        experiment_id: Optional experiment ID to filter chunks
        initial_k: Number of candidates from vector search
        final_k: Number of chunks after reranking
        use_reranking: Whether to apply LLM reranking
        top_k: Deprecated, use final_k instead

    Returns:
        List of most relevant chunks
    """
    # Backward compatibility: top_k overrides final_k if provided
    if top_k is not None:
        final_k = top_k
    query_embedding = get_embedding(query)

    # Stage 1: Vector search for candidates
    fetch_k = initial_k if use_reranking else final_k

    stmt = (
        select(Chunk)
        .where(Chunk.user_id == user_id)
        .order_by(Chunk.embedding.cosine_distance(query_embedding))
        .limit(fetch_k)
    )

    if project_id is not None:
        stmt = stmt.where(Chunk.project_id == project_id)
    if paper_id is not None:
        stmt = stmt.where(Chunk.paper_id == paper_id)
    if experiment_id is not None:
        stmt = stmt.where(Chunk.experiment_id == experiment_id)

    candidates = list(db.execute(stmt).scalars().all())

    # Stage 2: LLM reranking
    if use_reranking and len(candidates) > final_k:
        return llm_rerank(query, candidates, top_k=final_k)

    return candidates[:final_k]


def _build_enhanced_citation(chunk: Chunk, citation_number: int, snippet: str | None = None) -> dict:
    """Build an enhanced citation dict with full metadata.

    Args:
        chunk: The chunk being cited
        citation_number: The citation number (1, 2, 3, etc.)
        snippet: Optional extracted quote snippet

    Returns:
        Enhanced citation dict
    """
    # Build page numbers string
    page_numbers = None
    if chunk.page_start and chunk.page_end:
        if chunk.page_start == chunk.page_end:
            page_numbers = str(chunk.page_start)
        else:
            page_numbers = f"{chunk.page_start}-{chunk.page_end}"
    elif chunk.page_start:
        page_numbers = str(chunk.page_start)

    return {
        "chunk_id": chunk.id,
        "citation_number": citation_number,
        "paper_title": chunk.doc_title,
        "page_numbers": page_numbers,
        "section": chunk.section_title,
        "snippet": snippet or (chunk.content[:300] + "..." if len(chunk.content) > 300 else chunk.content),
        "chunk_index": chunk.chunk_index,
        "source_type": chunk.source_type,
        "source_id": chunk.source_id,
    }


def _extract_quotes_from_response(response_text: str) -> dict[int, str]:
    """Extract quoted snippets from LLM response.

    Parses the QUOTES USED section to get actual quotes.

    Args:
        response_text: Full LLM response

    Returns:
        Dict mapping citation number to quote text
    """
    quotes = {}

    # Look for QUOTES USED section
    quotes_section = re.search(r'QUOTES USED:\s*\n(.*)', response_text, re.DOTALL | re.IGNORECASE)
    if not quotes_section:
        return quotes

    quotes_text = quotes_section.group(1)

    # Parse individual quotes: [1]: "quote text"
    quote_pattern = r'\[(\d+)\]:\s*["\']([^"\']+)["\']'
    for match in re.finditer(quote_pattern, quotes_text):
        citation_num = int(match.group(1))
        quote = match.group(2).strip()
        quotes[citation_num] = quote

    return quotes


def _extract_answer_from_response(response_text: str) -> str:
    """Extract just the answer portion from a grounded response.

    Args:
        response_text: Full LLM response

    Returns:
        The answer text without the QUOTES USED section
    """
    # Check for ANSWER: prefix
    answer_match = re.search(r'ANSWER:\s*(.*?)(?=QUOTES USED:|$)', response_text, re.DOTALL | re.IGNORECASE)
    if answer_match:
        return answer_match.group(1).strip()

    # Fallback: remove QUOTES USED section if present
    quotes_start = re.search(r'\n\s*QUOTES USED:', response_text, re.IGNORECASE)
    if quotes_start:
        return response_text[:quotes_start.start()].strip()

    return response_text.strip()


def answer_question(
    db: Session,
    user_id: int,
    paper_id: int,
    question: str,
    top_k: int = 8,
) -> dict:
    """Answer a question about a paper using RAG with enhanced citations.

    Args:
        db: Database session
        user_id: User ID
        paper_id: Paper ID to query
        question: User's question
        top_k: Number of chunks to retrieve

    Returns:
        Dict with answer and enhanced citations including page numbers and snippets
    """
    # Retrieve relevant chunks with reranking
    chunks = retrieve_chunks(
        db, user_id, question,
        paper_id=paper_id,
        final_k=top_k,
        use_reranking=True
    )

    if not chunks:
        return {
            "answer": "No indexed content found for this paper. Please index the paper first.",
            "citations": [],
        }

    # Build context from chunks with metadata
    context_parts = []
    for i, chunk in enumerate(chunks):
        # Include section and page info in context
        metadata_parts = []
        if chunk.section_title:
            metadata_parts.append(f"Section: {chunk.section_title}")
        if chunk.page_start:
            if chunk.page_end and chunk.page_end != chunk.page_start:
                metadata_parts.append(f"Pages {chunk.page_start}-{chunk.page_end}")
            else:
                metadata_parts.append(f"Page {chunk.page_start}")

        metadata_str = f" ({', '.join(metadata_parts)})" if metadata_parts else ""
        context_parts.append(f"[{i + 1}]{metadata_str}:\n{chunk.content}")

    context = "\n\n".join(context_parts)

    # Call LLM with grounded system prompt
    client = OpenAI(api_key=settings.OPENAI_API_KEY)

    response = client.chat.completions.create(
        model=settings.OPENAI_MODEL,
        messages=[
            {"role": "system", "content": GROUNDED_SYSTEM_PROMPT},
            {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {question}"},
        ],
    )

    response_text = response.choices[0].message.content

    # Extract quotes from response
    quotes = _extract_quotes_from_response(response_text)

    # Build enhanced citations
    citations = []
    for i, chunk in enumerate(chunks):
        citation_num = i + 1
        snippet = quotes.get(citation_num)
        citations.append(_build_enhanced_citation(chunk, citation_num, snippet))

    # Extract clean answer
    answer = _extract_answer_from_response(response_text)

    return {
        "answer": answer,
        "citations": citations,
    }


def answer_project_question(
    db: Session,
    user_id: int,
    project_id: int,
    question: str,
    paper_id: int | None = None,
    top_k: int = 8,
) -> dict:
    """Answer a question across a project using RAG with enhanced citations.

    Args:
        db: Database session
        user_id: User ID
        project_id: Project ID to query
        question: User's question
        paper_id: Optional paper ID to further filter
        top_k: Number of chunks to retrieve

    Returns:
        Dict with answer and enhanced citations
    """
    chunks = retrieve_chunks(
        db, user_id, question,
        project_id=project_id,
        paper_id=paper_id,
        final_k=top_k,
        use_reranking=True
    )

    if not chunks:
        return {
            "answer": "No indexed content found for this project. Please index some papers or notes first.",
            "citations": [],
        }

    # Build context from chunks with source and metadata info
    context_parts = []
    for i, chunk in enumerate(chunks):
        # Build metadata string
        metadata_parts = [f"Source: {chunk.source_type}"]
        if chunk.doc_title:
            metadata_parts.append(f"Document: {chunk.doc_title}")
        if chunk.section_title:
            metadata_parts.append(f"Section: {chunk.section_title}")
        if chunk.page_start:
            if chunk.page_end and chunk.page_end != chunk.page_start:
                metadata_parts.append(f"Pages {chunk.page_start}-{chunk.page_end}")
            else:
                metadata_parts.append(f"Page {chunk.page_start}")

        metadata_str = f" ({', '.join(metadata_parts)})"
        context_parts.append(f"[{i + 1}]{metadata_str}:\n{chunk.content}")

    context = "\n\n".join(context_parts)

    client = OpenAI(api_key=settings.OPENAI_API_KEY)

    # Enhanced system prompt for project-wide queries
    project_system_prompt = """You are a research assistant. Answer ONLY using the provided context from multiple documents in this project.

CRITICAL RULES:
1. If information is NOT in the context, respond: "This information was not found in the provided documents."
2. Only make claims that are directly supported by the context.
3. Write your answer as clean prose WITHOUT inline citation markers like [1], [2], etc.
4. After your answer, list the exact quotes you used from each numbered source.

Format your response as:
ANSWER: [Your answer as clean prose, no citation markers]

QUOTES USED:
[1]: "exact quote from source 1"
[2]: "exact quote from source 2"
"""

    response = client.chat.completions.create(
        model=settings.OPENAI_MODEL,
        messages=[
            {"role": "system", "content": project_system_prompt},
            {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {question}"},
        ],
    )

    response_text = response.choices[0].message.content

    # Extract quotes and build citations
    quotes = _extract_quotes_from_response(response_text)

    citations = []
    for i, chunk in enumerate(chunks):
        citation_num = i + 1
        snippet = quotes.get(citation_num)
        citations.append(_build_enhanced_citation(chunk, citation_num, snippet))

    answer = _extract_answer_from_response(response_text)

    return {
        "answer": answer,
        "citations": citations,
    }
