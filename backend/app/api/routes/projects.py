import secrets
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import select, func, or_
from sqlalchemy.exc import IntegrityError

from app.deps import get_db, get_current_user, get_project_for_user, require_project_owner
from app.models import Project
from app.models.user import User
from app.models.project_member import ProjectMember
from app.models.project_invite import ProjectInvite
from app.schemas.project import (
    ProjectCreate, ProjectUpdate, ProjectOut,
    ProjectMemberOut, ProjectInviteCreate, ProjectInviteOut, InviteJoin,
)
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

        # Also create an owner membership row
        member = ProjectMember(project_id=project.id, user_id=user_id, role="owner")
        db.add(member)
        db.commit()

    return project


def _project_to_out(project: Project, role: str, db: Session) -> dict:
    """Convert a Project to a ProjectOut-compatible dict with role and member_count."""
    member_count = db.execute(
        select(func.count()).select_from(ProjectMember).where(ProjectMember.project_id == project.id)
    ).scalar()
    return {
        "id": project.id,
        "user_id": project.user_id,
        "name": project.name,
        "description": project.description,
        "created_at": project.created_at,
        "updated_at": project.updated_at,
        "role": role,
        "member_count": member_count,
    }


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

    # Create owner membership
    member = ProjectMember(project_id=project.id, user_id=user_id, role="owner")
    db.add(member)
    db.commit()

    return _project_to_out(project, "owner", db)


@router.get("", response_model=list[ProjectOut])
def list_projects(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    user_id = current_user.id

    # Projects where user is owner OR member
    member_project_ids = select(ProjectMember.project_id).where(ProjectMember.user_id == user_id)

    stmt = (
        select(Project)
        .where(
            or_(
                Project.user_id == user_id,
                Project.id.in_(member_project_ids),
            )
        )
        .order_by(Project.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    projects = list(db.execute(stmt).scalars().all())

    result = []
    for project in projects:
        # Determine role
        if project.user_id == user_id:
            role = "owner"
        else:
            member_stmt = select(ProjectMember.role).where(
                ProjectMember.project_id == project.id,
                ProjectMember.user_id == user_id,
            )
            role = db.execute(member_stmt).scalar_one_or_none() or "member"
        result.append(_project_to_out(project, role, db))

    return result


@router.get("/{project_id}", response_model=ProjectOut)
def get_project(project_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    project, role = get_project_for_user(project_id, db, current_user)
    return _project_to_out(project, role, db)


@router.patch("/{project_id}", response_model=ProjectOut)
def update_project(project_id: int, payload: ProjectUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    project = require_project_owner(project_id, db, current_user)

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

    return _project_to_out(project, "owner", db)


@router.delete("/{project_id}")
def delete_project(project_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    project = require_project_owner(project_id, db, current_user)

    if project.name == "Default":
        raise HTTPException(status_code=400, detail="Cannot delete the default project")

    db.delete(project)
    db.commit()
    return {"deleted": True, "project_id": project_id}


@router.post("/{project_id}/qa")
async def qa_project_endpoint(
    project_id: int,
    question: str = Query(..., min_length=1),
    paper_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Ask a question across all indexed content in a project."""
    project, role = get_project_for_user(project_id, db, current_user)

    try:
        result = await answer_project_question(db, current_user.id, project_id, question, paper_id=paper_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"QA failed: {str(e)}")


# --- Members ---

@router.get("/{project_id}/members", response_model=list[ProjectMemberOut])
def list_members(project_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """List all members of a project. Accessible to owner and members."""
    get_project_for_user(project_id, db, current_user)

    stmt = (
        select(ProjectMember, User.email)
        .join(User, ProjectMember.user_id == User.id)
        .where(ProjectMember.project_id == project_id)
        .order_by(ProjectMember.added_at)
    )
    rows = db.execute(stmt).all()

    return [
        {
            "id": member.id,
            "user_id": member.user_id,
            "email": email,
            "role": member.role,
            "added_at": member.added_at,
        }
        for member, email in rows
    ]


@router.delete("/{project_id}/members/{user_id}")
def remove_member(
    project_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Remove a member from a project. Owner can remove anyone (except themselves). Members can remove themselves."""
    project, role = get_project_for_user(project_id, db, current_user)

    # Owner cannot remove themselves via this endpoint
    if user_id == project.user_id:
        raise HTTPException(status_code=400, detail="Cannot remove the project owner")

    # Non-owners can only remove themselves
    if role != "owner" and user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only the project owner can remove other members")

    stmt = select(ProjectMember).where(
        ProjectMember.project_id == project_id,
        ProjectMember.user_id == user_id,
    )
    member = db.execute(stmt).scalar_one_or_none()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    db.delete(member)
    db.commit()
    return {"removed": True, "user_id": user_id}


# --- Invites ---

@router.post("/{project_id}/invites", response_model=ProjectInviteOut)
def create_invite(
    project_id: int,
    payload: ProjectInviteCreate = ProjectInviteCreate(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate an invite code for the project. Owner only."""
    require_project_owner(project_id, db, current_user)

    code = secrets.token_urlsafe(12)[:16]

    invite = ProjectInvite(
        project_id=project_id,
        code=code,
        created_by=current_user.id,
        expires_at=payload.expires_at,
    )
    db.add(invite)
    db.commit()
    db.refresh(invite)
    return invite


@router.get("/{project_id}/invites", response_model=list[ProjectInviteOut])
def list_invites(project_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """List active invites for a project. Owner only."""
    require_project_owner(project_id, db, current_user)

    stmt = (
        select(ProjectInvite)
        .where(ProjectInvite.project_id == project_id, ProjectInvite.is_active == True)
        .order_by(ProjectInvite.created_at.desc())
    )
    return list(db.execute(stmt).scalars().all())


@router.delete("/{project_id}/invites/{invite_id}")
def revoke_invite(
    project_id: int,
    invite_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Revoke an invite code. Owner only."""
    require_project_owner(project_id, db, current_user)

    stmt = select(ProjectInvite).where(
        ProjectInvite.id == invite_id,
        ProjectInvite.project_id == project_id,
    )
    invite = db.execute(stmt).scalar_one_or_none()
    if not invite:
        raise HTTPException(status_code=404, detail="Invite not found")

    invite.is_active = False
    db.commit()
    return {"revoked": True, "invite_id": invite_id}


@router.post("/join")
def join_project(
    payload: InviteJoin,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Join a project using an invite code."""
    stmt = select(ProjectInvite).where(
        ProjectInvite.code == payload.code,
        ProjectInvite.is_active == True,
    )
    invite = db.execute(stmt).scalar_one_or_none()
    if not invite:
        raise HTTPException(status_code=404, detail="Invalid or expired invite code")

    # Check expiry
    if invite.expires_at and invite.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="This invite code has expired")

    # Check if already a member
    existing = db.execute(
        select(ProjectMember).where(
            ProjectMember.project_id == invite.project_id,
            ProjectMember.user_id == current_user.id,
        )
    ).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail="You are already a member of this project")

    member = ProjectMember(
        project_id=invite.project_id,
        user_id=current_user.id,
        role="member",
    )
    db.add(member)
    db.commit()

    return {"joined": True, "project_id": invite.project_id}
