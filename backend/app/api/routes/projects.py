from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.deps import get_db, get_current_user
from app.models import Project
from app.models.user import User
from app.schemas.project import ProjectCreate, ProjectUpdate, ProjectOut
from app.services.rag import answer_project_question

router = APIRouter(prefix="/projects", tags=["projects"])


def get_or_create_default_project(db: Session, user_id: int) -> Project:
    """Get or create the default project for a user."""
    stmt = select(Project).where(Project.user_id == user_id, Project.name == "Default")
    project = db.execute(stmt).scalar_one_or_none()

    if not project:
        project = Project(user_id=user_id, name="Default", description="Default project for unassigned items")
        db.add(project)
        db.commit()
        db.refresh(project)

    return project


@router.post("", response_model=ProjectOut)
def create_project(payload: ProjectCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    user_id = current_user.id

    project = Project(
        user_id=user_id,
        name=payload.name,
        description=payload.description,
    )

    try:
        db.add(project)
        db.commit()
        db.refresh(project)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="A project with this name already exists")

    return project


@router.get("", response_model=list[ProjectOut])
def list_projects(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    user_id = current_user.id

    stmt = (
        select(Project)
        .where(Project.user_id == user_id)
        .order_by(Project.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    return list(db.execute(stmt).scalars().all())


@router.get("/{project_id}", response_model=ProjectOut)
def get_project(project_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    user_id = current_user.id

    stmt = select(Project).where(Project.id == project_id, Project.user_id == user_id)
    project = db.execute(stmt).scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.patch("/{project_id}", response_model=ProjectOut)
def update_project(project_id: int, payload: ProjectUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    user_id = current_user.id

    stmt = select(Project).where(Project.id == project_id, Project.user_id == user_id)
    project = db.execute(stmt).scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if payload.name is not None:
        project.name = payload.name
    if payload.description is not None:
        project.description = payload.description

    try:
        db.commit()
        db.refresh(project)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="A project with this name already exists")

    return project


@router.delete("/{project_id}")
def delete_project(project_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    user_id = current_user.id

    stmt = select(Project).where(Project.id == project_id, Project.user_id == user_id)
    project = db.execute(stmt).scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if project.name == "Default":
        raise HTTPException(status_code=400, detail="Cannot delete the default project")

    db.delete(project)
    db.commit()
    return {"deleted": True, "project_id": project_id}


@router.post("/{project_id}/qa")
def qa_project_endpoint(
    project_id: int,
    question: str = Query(..., min_length=1),
    paper_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Ask a question across all indexed content in a project."""
    user_id = current_user.id

    stmt = select(Project).where(Project.id == project_id, Project.user_id == user_id)
    project = db.execute(stmt).scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    try:
        result = answer_project_question(db, user_id, project_id, question, paper_id=paper_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"QA failed: {str(e)}")
