import asyncio
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy import select, func

from app.deps import get_db, get_current_user, get_project_for_user
from app.models import Paper, Project
from app.models.user import User
from app.models.project_member import ProjectMember
from app.models.paper import ProcessingStatus
from app.models.chunk import Chunk
from app.schemas.paper import PaperUpdate, PaperOut
from app.services.pdf_extractor import extract_pages_from_bytes, get_first_n_chars
from app.services.llm_extractor import extract_paper_metadata
from app.services.rag import index_paper_with_sections, answer_question
from app.services.embedding import parse_document_sections
from app.api.routes.projects import get_or_create_default_project
from app.core.config import settings

router = APIRouter(prefix="/papers", tags=["papers"])


def _get_accessible_project_ids(db: Session, user_id: int) -> list[int]:
    """Get all project IDs the user has access to (owned or member of)."""
    stmt = select(Project.id).where(Project.user_id == user_id)
    owned = [row[0] for row in db.execute(stmt).all()]

    stmt = select(ProjectMember.project_id).where(ProjectMember.user_id == user_id)
    member_of = [row[0] for row in db.execute(stmt).all()]

    return list(set(owned + member_of))


def _get_paper_with_access(db: Session, paper_id: int, user: User) -> Paper:
    """Get a paper and verify the user has access via project membership."""
    stmt = select(Paper).where(Paper.id == paper_id)
    paper = db.execute(stmt).scalar_one_or_none()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")

    # Check access: user owns the paper, or has access to the paper's project
    if paper.user_id == user.id:
        return paper

    if paper.project_id:
        try:
            get_project_for_user(paper.project_id, db, user)
            return paper
        except HTTPException:
            pass

    raise HTTPException(status_code=404, detail="Paper not found")


def compute_is_indexed(db: Session, paper_id: int) -> bool:
    """Check if a paper has any chunks indexed for RAG."""
    count = db.execute(
        select(func.count()).select_from(Chunk).where(Chunk.paper_id == paper_id)
    ).scalar()
    return count > 0

@router.post("/upload", response_model=PaperOut)
async def upload_paper(
    file: UploadFile = File(...),
    project_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    user_id = current_user.id

    # Default to "Default" project if not specified
    if project_id is None:
        default_project = get_or_create_default_project(db, user_id)
        project_id = default_project.id
    else:
        # Verify user has access to the target project
        get_project_for_user(project_id, db, current_user)

    if file.content_type not in {"application/pdf"}:
        raise HTTPException(status_code=400, detail="Only PDF uploads are allowed")

    pdf_bytes = await file.read()

    max_bytes = settings.MAX_UPLOAD_MB * 1024 * 1024
    if len(pdf_bytes) > max_bytes:
        raise HTTPException(status_code=413, detail=f"File too large (max {settings.MAX_UPLOAD_MB} MB)")

    # Extract text and pages from PDF bytes (no file storage)
    try:
        pages = await extract_pages_from_bytes(pdf_bytes)
        full_text = "\n".join(p["text"] for p in pages)
        truncated_text = get_first_n_chars(full_text, 8000)

        # Run metadata extraction and section parsing in parallel
        metadata_task = extract_paper_metadata(truncated_text)
        sections_task = parse_document_sections(full_text)
        metadata, sections = await asyncio.gather(metadata_task, sections_task)

        paper = Paper(
            user_id=user_id,
            project_id=project_id,
            title=metadata.title,
            abstract=metadata.abstract,
            extracted_text=full_text,
            processing_status=ProcessingStatus.COMPLETED.value,
        )
        db.add(paper)
        db.commit()
        db.refresh(paper)

        # Index immediately for RAG (pass pre-parsed sections and pages)
        await index_paper_with_sections(db, paper, sections=sections, pages=pages)

    except Exception as e:
        # If extraction/indexing fails, save with filename as title
        paper = Paper(
            user_id=user_id,
            project_id=project_id,
            title=file.filename,
            processing_status=ProcessingStatus.FAILED.value,
            processing_error=str(e),
        )
        db.add(paper)
        db.commit()
        db.refresh(paper)

    return paper


@router.get("", response_model=list[PaperOut])
def list_papers(
    project_id: int | None = Query(default=None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    user_id = current_user.id

    if project_id is not None:
        # Verify access to the specific project
        get_project_for_user(project_id, db, current_user)
        stmt = select(Paper).where(Paper.project_id == project_id)
    else:
        # Return papers from all accessible projects
        accessible_ids = _get_accessible_project_ids(db, user_id)
        stmt = select(Paper).where(Paper.project_id.in_(accessible_ids))

    stmt = stmt.order_by(Paper.id.desc()).limit(limit).offset(offset)
    papers = list(db.execute(stmt).scalars().all())

    # Add is_indexed_for_rag to each paper
    result = []
    for paper in papers:
        paper_dict = {
            "id": paper.id,
            "user_id": paper.user_id,
            "project_id": paper.project_id,
            "title": paper.title,
            "abstract": paper.abstract,
            "pdf_path": paper.pdf_path,
            "processing_status": paper.processing_status,
            "processing_error": paper.processing_error,
            "is_indexed_for_rag": compute_is_indexed(db, paper.id),
        }
        result.append(paper_dict)
    return result

@router.get("/{paper_id}", response_model=PaperOut)
def get_paper(paper_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    paper = _get_paper_with_access(db, paper_id, current_user)

    return {
        "id": paper.id,
        "user_id": paper.user_id,
        "project_id": paper.project_id,
        "title": paper.title,
        "abstract": paper.abstract,
        "pdf_path": paper.pdf_path,
        "processing_status": paper.processing_status,
        "processing_error": paper.processing_error,
        "is_indexed_for_rag": compute_is_indexed(db, paper.id),
    }


@router.patch("/{paper_id}", response_model=PaperOut)
def update_paper(paper_id: int, payload: PaperUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    paper = _get_paper_with_access(db, paper_id, current_user)

    if payload.title is not None:
        paper.title = payload.title
    if payload.abstract is not None:
        paper.abstract = payload.abstract

    db.commit()
    db.refresh(paper)
    return paper

@router.delete("/{paper_id}")
def delete_paper(paper_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    paper = _get_paper_with_access(db, paper_id, current_user)

    db.delete(paper)
    db.commit()
    return {"deleted": True, "paper_id": paper_id}


@router.post("/{paper_id}/index")
async def index_paper_endpoint(paper_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Index a paper's text into chunks with embeddings for RAG."""
    paper = _get_paper_with_access(db, paper_id, current_user)

    if not paper.extracted_text:
        raise HTTPException(status_code=400, detail="Paper has no extracted text to index")

    try:
        sections = await parse_document_sections(paper.extracted_text)
        num_chunks = await index_paper_with_sections(db, paper, sections=sections)
        return {"indexed": True, "paper_id": paper_id, "chunks_created": num_chunks}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Indexing failed: {str(e)}")


@router.post("/{paper_id}/qa")
async def qa_paper_endpoint(
    paper_id: int,
    question: str = Query(..., min_length=1),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Ask a question about a paper using RAG."""
    paper = _get_paper_with_access(db, paper_id, current_user)

    try:
        result = await answer_question(db, current_user.id, paper_id, question)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"QA failed: {str(e)}")
