from sqlalchemy.orm import Session
from sqlalchemy import select, delete
from openai import OpenAI

from app.core.config import settings
from app.models import Paper, Chunk, ChunkSource
from app.services.embedding import chunk_text, get_embeddings, get_embedding


def index_paper(db: Session, paper: Paper) -> int:
    """Index a paper's extracted text into chunks with embeddings.

    Args:
        db: Database session
        paper: Paper to index (must have extracted_text)

    Returns:
        Number of chunks created
    """
    if not paper.extracted_text:
        raise ValueError("Paper has no extracted text to index")

    # Delete existing chunks for this paper
    db.execute(
        delete(Chunk).where(
            Chunk.paper_id == paper.id,
            Chunk.source_type == ChunkSource.PAPER.value
        )
    )

    # Chunk the text
    chunks = chunk_text(paper.extracted_text)

    if not chunks:
        return 0

    # Get embeddings for all chunks in one API call
    embeddings = get_embeddings(chunks)

    # Create chunk records
    for i, (content, embedding) in enumerate(zip(chunks, embeddings)):
        chunk = Chunk(
            user_id=paper.user_id,
            source_type=ChunkSource.PAPER.value,
            paper_id=paper.id,
            content=content,
            chunk_index=i,
            embedding=embedding,
        )
        db.add(chunk)

    db.commit()
    return len(chunks)


def retrieve_chunks(
    db: Session,
    user_id: int,
    query: str,
    paper_id: int | None = None,
    top_k: int = 5,
) -> list[Chunk]:
    """Retrieve the most relevant chunks for a query.

    Args:
        db: Database session
        user_id: User ID to filter chunks
        query: Query text to search for
        paper_id: Optional paper ID to filter chunks
        top_k: Number of chunks to retrieve

    Returns:
        List of most relevant chunks
    """
    query_embedding = get_embedding(query)

    # Build query using pgvector's cosine distance
    stmt = (
        select(Chunk)
        .where(Chunk.user_id == user_id)
        .order_by(Chunk.embedding.cosine_distance(query_embedding))
        .limit(top_k)
    )

    if paper_id is not None:
        stmt = stmt.where(Chunk.paper_id == paper_id)

    return list(db.execute(stmt).scalars().all())


def answer_question(
    db: Session,
    user_id: int,
    paper_id: int,
    question: str,
    top_k: int = 5,
) -> dict:
    """Answer a question about a paper using RAG.

    Args:
        db: Database session
        user_id: User ID
        paper_id: Paper ID to query
        question: User's question
        top_k: Number of chunks to retrieve

    Returns:
        Dict with answer and citations
    """
    # Retrieve relevant chunks
    chunks = retrieve_chunks(db, user_id, question, paper_id=paper_id, top_k=top_k)

    if not chunks:
        return {
            "answer": "No indexed content found for this paper. Please index the paper first.",
            "citations": [],
        }

    # Build context from chunks
    context_parts = []
    citations = []
    for i, chunk in enumerate(chunks):
        context_parts.append(f"[{i + 1}] {chunk.content}")
        citations.append({
            "chunk_id": chunk.id,
            "chunk_index": chunk.chunk_index,
            "content_preview": chunk.content[:200] + "..." if len(chunk.content) > 200 else chunk.content,
        })

    context = "\n\n".join(context_parts)

    # Call LLM to generate answer
    client = OpenAI(api_key=settings.OPENAI_API_KEY)

    system_prompt = """You are a helpful research assistant. Answer the user's question based on the provided context from a research paper.

Rules:
1. Only use information from the provided context
2. If the context doesn't contain enough information to answer, say so
3. Cite your sources using [1], [2], etc. corresponding to the context chunks
4. Be concise but thorough"""

    response = client.chat.completions.create(
        model=settings.OPENAI_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {question}"},
        ],
    )

    return {
        "answer": response.choices[0].message.content,
        "citations": citations,
    }
