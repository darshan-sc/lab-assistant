from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.db import get_db
from app.models import Note, Paper
from app.schemas.note import NoteCreate, NoteUpdate, Note as NoteOut

router = APIRouter(prefix="/notes", tags=["notes"])


# TEMP: until auth exists
def get_current_user_id() -> int:
    return 1


@router.post("", response_model=NoteOut)
def create_note(payload: NoteCreate, db: Session = Depends(get_db)):
    user_id = get_current_user_id()

    # Verify paper exists and belongs to user if paper_id provided
    if payload.paper_id:
        stmt = select(Paper).where(Paper.id == payload.paper_id, Paper.user_id == user_id)
        paper = db.execute(stmt).scalar_one_or_none()
        if not paper:
            raise HTTPException(status_code=404, detail="Paper not found")

    note = Note(
        user_id=user_id,
        paper_id=payload.paper_id,
        experiment_id=payload.experiment_id,
        content=payload.content,
    )
    db.add(note)
    db.commit()
    db.refresh(note)
    return note


@router.get("", response_model=list[NoteOut])
def list_notes(
    paper_id: int | None = Query(default=None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    user_id = get_current_user_id()

    stmt = select(Note).where(Note.user_id == user_id)

    if paper_id is not None:
        stmt = stmt.where(Note.paper_id == paper_id)

    stmt = stmt.order_by(Note.created_at.desc()).limit(limit).offset(offset)
    return list(db.execute(stmt).scalars().all())


@router.patch("/{note_id}", response_model=NoteOut)
def update_note(note_id: int, payload: NoteUpdate, db: Session = Depends(get_db)):
    user_id = get_current_user_id()

    stmt = select(Note).where(Note.id == note_id, Note.user_id == user_id)
    note = db.execute(stmt).scalar_one_or_none()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")

    if payload.content is not None:
        note.content = payload.content

    db.commit()
    db.refresh(note)
    return note


@router.delete("/{note_id}")
def delete_note(note_id: int, db: Session = Depends(get_db)):
    user_id = get_current_user_id()

    stmt = select(Note).where(Note.id == note_id, Note.user_id == user_id)
    note = db.execute(stmt).scalar_one_or_none()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")

    db.delete(note)
    db.commit()
    return {"deleted": True, "note_id": note_id}
