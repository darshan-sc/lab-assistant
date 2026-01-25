from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy import select, func

from app.deps import get_db, get_current_user
from app.models import Paper
from app.models.user import User
from app.models.paper import ProcessingStatus
from app.models.chunk import Chunk
from app.schemas.paper import PaperUpdate, PaperOut
from app.services.storage import save_upload_pdf
from app.services.pdf_extractor import extract_text_from_pdf, get_first_n_chars
from app.services.llm_extractor import extract_paper_metadata
from app.services.rag import index_paper, answer_question
from app.api.routes.projects import get_or_create_default_project
from app.core.config import settings

router = APIRouter(prefix="/papers", tags=["papers"])


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

    if file.content_type not in {"application/pdf"}:
        raise HTTPException(status_code=400, detail="Only PDF uploads are allowed")

    data = await file.read()

    max_bytes = settings.MAX_UPLOAD_MB * 1024 * 1024
    if len(data) > max_bytes:
        raise HTTPException(status_code=413, detail=f"File too large (max {settings.MAX_UPLOAD_MB} MB)")

    path = save_upload_pdf(data, file.filename)

    # Extract text from PDF (path is already the full path)
    try:
        full_text = extract_text_from_pdf(path)
        truncated_text = get_first_n_chars(full_text, 8000)
        metadata = extract_paper_metadata(truncated_text)

        paper = Paper(
            user_id=user_id,
            project_id=project_id,
            pdf_path=path,
            title=metadata.title,
            abstract=metadata.abstract,
            extracted_text=full_text,
            processing_status=ProcessingStatus.COMPLETED.value,
        )
    except Exception as e:
        # If extraction fails, save with filename as title
        paper = Paper(
            user_id=user_id,
            project_id=project_id,
            pdf_path=path,
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

    stmt = select(Paper).where(Paper.user_id == user_id)

    if project_id is not None:
        stmt = stmt.where(Paper.project_id == project_id)

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
    user_id = current_user.id

    stmt = select(Paper).where(Paper.id == paper_id, Paper.user_id == user_id)
    paper = db.execute(stmt).scalar_one_or_none()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")

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
    user_id = current_user.id

    stmt = select(Paper).where(Paper.id == paper_id, Paper.user_id == user_id)
    paper = db.execute(stmt).scalar_one_or_none()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")

    if payload.title is not None:
        paper.title = payload.title
    if payload.abstract is not None:
        paper.abstract = payload.abstract

    db.commit()
    db.refresh(paper)
    return paper

@router.delete("/{paper_id}")
def delete_paper(paper_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    user_id = current_user.id

    stmt = select(Paper).where(Paper.id == paper_id, Paper.user_id == user_id)
    paper = db.execute(stmt).scalar_one_or_none()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")

    db.delete(paper)
    db.commit()
    return {"deleted": True, "paper_id": paper_id}


@router.post("/{paper_id}/index")
def index_paper_endpoint(paper_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Index a paper's text into chunks with embeddings for RAG."""
    user_id = current_user.id

    stmt = select(Paper).where(Paper.id == paper_id, Paper.user_id == user_id)
    paper = db.execute(stmt).scalar_one_or_none()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")

    if not paper.extracted_text:
        raise HTTPException(status_code=400, detail="Paper has no extracted text to index")

    try:
        num_chunks = index_paper(db, paper)
        return {"indexed": True, "paper_id": paper_id, "chunks_created": num_chunks}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Indexing failed: {str(e)}")


@router.post("/{paper_id}/qa")
def qa_paper_endpoint(
    paper_id: int,
    question: str = Query(..., min_length=1),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Ask a question about a paper using RAG."""
    user_id = current_user.id

    stmt = select(Paper).where(Paper.id == paper_id, Paper.user_id == user_id)
    paper = db.execute(stmt).scalar_one_or_none()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")

    try:
        result = answer_question(db, user_id, paper_id, question)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"QA failed: {str(e)}")
