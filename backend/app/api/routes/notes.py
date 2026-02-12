from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.deps import get_db, get_current_user, get_project_for_user
from app.models import Note, Paper, Project
from app.models.user import User
from app.models.project_member import ProjectMember
from app.schemas.note import NoteCreate, NoteUpdate, NoteOut
from app.api.routes.projects import get_or_create_default_project

router = APIRouter(prefix="/notes", tags=["notes"])


def _get_accessible_project_ids(db: Session, user_id: int) -> list[int]:
    """Get all project IDs the user has access to (owned or member of)."""
    stmt = select(Project.id).where(Project.user_id == user_id)
    owned = [row[0] for row in db.execute(stmt).all()]

    stmt = select(ProjectMember.project_id).where(ProjectMember.user_id == user_id)
    member_of = [row[0] for row in db.execute(stmt).all()]

    return list(set(owned + member_of))


def _get_note_with_access(db: Session, note_id: int, user: User) -> Note:
    """Get a note and verify user has access via project membership."""
    stmt = select(Note).where(Note.id == note_id)
    note = db.execute(stmt).scalar_one_or_none()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")

    if note.user_id == user.id:
        return note

    if note.project_id:
        try:
            get_project_for_user(note.project_id, db, user)
            return note
        except HTTPException:
            pass

    raise HTTPException(status_code=404, detail="Note not found")


@router.post("", response_model=NoteOut)
def create_note(payload: NoteCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    user_id = current_user.id

    # Verify paper exists and user has access if paper_id provided
    if payload.paper_id:
        stmt = select(Paper).where(Paper.id == payload.paper_id)
        paper = db.execute(stmt).scalar_one_or_none()
        if not paper:
            raise HTTPException(status_code=404, detail="Paper not found")
        # Check access via paper's project
        if paper.user_id != user_id and paper.project_id:
            get_project_for_user(paper.project_id, db, current_user)

    # Default to "Default" project if not specified
    project_id = payload.project_id
    if project_id is None:
        default_project = get_or_create_default_project(db, user_id)
        project_id = default_project.id
    else:
        # Verify access to the target project
        get_project_for_user(project_id, db, current_user)

    note = Note(
        user_id=user_id,
        project_id=project_id,
        paper_id=payload.paper_id,
        experiment_id=payload.experiment_id,
        experiment_run_id=payload.experiment_run_id,
        content=payload.content,
    )
    db.add(note)
    db.commit()
    db.refresh(note)
    return note


@router.get("", response_model=list[NoteOut])
def list_notes(
    project_id: int | None = Query(default=None),
    paper_id: int | None = Query(default=None),
    experiment_id: int | None = Query(default=None),
    experiment_run_id: int | None = Query(default=None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    user_id = current_user.id

    if project_id is not None:
        # Verify access to the specific project
        get_project_for_user(project_id, db, current_user)
        stmt = select(Note).where(Note.project_id == project_id)
    else:
        # Return notes from all accessible projects
        accessible_ids = _get_accessible_project_ids(db, user_id)
        stmt = select(Note).where(Note.project_id.in_(accessible_ids))

    if paper_id is not None:
        stmt = stmt.where(Note.paper_id == paper_id)
    if experiment_id is not None:
        stmt = stmt.where(Note.experiment_id == experiment_id)
    if experiment_run_id is not None:
        stmt = stmt.where(Note.experiment_run_id == experiment_run_id)

    stmt = stmt.order_by(Note.created_at.desc()).limit(limit).offset(offset)
    return list(db.execute(stmt).scalars().all())


@router.patch("/{note_id}", response_model=NoteOut)
def update_note(note_id: int, payload: NoteUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    note = _get_note_with_access(db, note_id, current_user)

    if payload.content is not None:
        note.content = payload.content

    db.commit()
    db.refresh(note)
    return note


@router.delete("/{note_id}")
def delete_note(note_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    note = _get_note_with_access(db, note_id, current_user)

    db.delete(note)
    db.commit()
    return {"deleted": True, "note_id": note_id}
