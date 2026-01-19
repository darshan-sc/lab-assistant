from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.db import get_db
from app.models import Paper
from app.schemas.paper import PaperUpdate, PaperOut
from app.services.storage import save_upload_pdf
from app.core.config import settings

router = APIRouter(prefix="/papers", tags=["papers"])

# TEMP: until auth exists
def get_current_user_id() -> int:
    return 1

@router.post("/upload", response_model=PaperOut)
async def upload_paper(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    user_id = get_current_user_id()

    if file.content_type not in {"application/pdf"}:
        raise HTTPException(status_code=400, detail="Only PDF uploads are allowed")

    data = await file.read()

    max_bytes = settings.MAX_UPLOAD_MB * 1024 * 1024
    if len(data) > max_bytes:
        raise HTTPException(status_code=413, detail=f"File too large (max {settings.MAX_UPLOAD_MB} MB)")

    path = save_upload_pdf(data, file.filename)

    paper = Paper(
        user_id=user_id,
        pdf_path=path,
        title=file.filename, # Use filename as temporary title
        # abstract stays null until extraction
    )
    db.add(paper)
    db.commit()
    db.refresh(paper)
    return paper


@router.get("", response_model=list[PaperOut])
def list_papers(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    user_id = get_current_user_id()

    stmt = (
        select(Paper)
        .where(Paper.user_id == user_id)
        .order_by(Paper.id.desc())
        .limit(limit)
        .offset(offset)
    )
    return list(db.execute(stmt).scalars().all())

@router.get("/{paper_id}", response_model=PaperOut)
def get_paper(paper_id: int, db: Session = Depends(get_db)):
    user_id = get_current_user_id()

    stmt = select(Paper).where(Paper.id == paper_id, Paper.user_id == user_id)
    paper = db.execute(stmt).scalar_one_or_none()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    return paper

@router.patch("/{paper_id}", response_model=PaperOut)
def update_paper(paper_id: int, payload: PaperUpdate, db: Session = Depends(get_db)):
    user_id = get_current_user_id()

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
def delete_paper(paper_id: int, db: Session = Depends(get_db)):
    user_id = get_current_user_id()

    stmt = select(Paper).where(Paper.id == paper_id, Paper.user_id == user_id)
    paper = db.execute(stmt).scalar_one_or_none()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")

    db.delete(paper)
    db.commit()
    return {"deleted": True, "paper_id": paper_id}
