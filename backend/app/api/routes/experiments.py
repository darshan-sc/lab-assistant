from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.deps import get_db, get_current_user, get_project_for_user
from app.models import Project, Experiment, ExperimentRun
from app.models.user import User
from app.models.project_member import ProjectMember
from app.schemas.experiment import (
    ExperimentCreate, ExperimentUpdate, ExperimentOut,
    RunCreate, RunUpdate, RunOut,
)
from app.api.routes.projects import get_or_create_default_project

router = APIRouter(tags=["experiments"])


def _get_experiment_with_access(db: Session, experiment_id: int, user: User) -> Experiment:
    """Get an experiment and verify the user has access via project membership."""
    stmt = select(Experiment).where(Experiment.id == experiment_id)
    experiment = db.execute(stmt).scalar_one_or_none()
    if not experiment:
        raise HTTPException(status_code=404, detail="Experiment not found")

    if experiment.user_id == user.id:
        return experiment

    if experiment.project_id:
        try:
            get_project_for_user(experiment.project_id, db, user)
            return experiment
        except HTTPException:
            pass

    raise HTTPException(status_code=404, detail="Experiment not found")


def _get_run_with_access(db: Session, run_id: int, user: User) -> ExperimentRun:
    """Get a run and verify the user has access via experiment's project membership."""
    stmt = select(ExperimentRun).where(ExperimentRun.id == run_id)
    run = db.execute(stmt).scalar_one_or_none()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    if run.user_id == user.id:
        return run

    if run.project_id:
        try:
            get_project_for_user(run.project_id, db, user)
            return run
        except HTTPException:
            pass

    raise HTTPException(status_code=404, detail="Run not found")


# --- Experiment Groups ---

@router.post("/projects/{project_id}/experiments", response_model=ExperimentOut)
def create_experiment(
    project_id: int,
    payload: ExperimentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Verify project access
    get_project_for_user(project_id, db, current_user)

    experiment = Experiment(
        user_id=current_user.id,
        project_id=project_id,
        title=payload.title,
        goal=payload.goal,
        protocol=payload.protocol,
        paper_id=payload.paper_id,
    )
    db.add(experiment)
    db.commit()
    db.refresh(experiment)
    return experiment


@router.get("/projects/{project_id}/experiments", response_model=list[ExperimentOut])
def list_experiments(
    project_id: int,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Verify project access
    get_project_for_user(project_id, db, current_user)

    stmt = (
        select(Experiment)
        .where(Experiment.project_id == project_id)
        .order_by(Experiment.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    return list(db.execute(stmt).scalars().all())


@router.get("/experiments/{experiment_id}", response_model=ExperimentOut)
def get_experiment(experiment_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return _get_experiment_with_access(db, experiment_id, current_user)


@router.patch("/experiments/{experiment_id}", response_model=ExperimentOut)
def update_experiment(
    experiment_id: int,
    payload: ExperimentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    experiment = _get_experiment_with_access(db, experiment_id, current_user)

    if payload.title is not None:
        experiment.title = payload.title
    if payload.goal is not None:
        experiment.goal = payload.goal
    if payload.protocol is not None:
        experiment.protocol = payload.protocol
    if payload.results is not None:
        experiment.results = payload.results
    if payload.status is not None:
        experiment.status = payload.status
    if payload.paper_id is not None:
        experiment.paper_id = payload.paper_id

    db.commit()
    db.refresh(experiment)
    return experiment


@router.delete("/experiments/{experiment_id}")
def delete_experiment(experiment_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    experiment = _get_experiment_with_access(db, experiment_id, current_user)

    db.delete(experiment)
    db.commit()
    return {"deleted": True, "experiment_id": experiment_id}


# --- Experiment Runs ---

@router.post("/experiments/{experiment_id}/runs", response_model=RunOut)
def create_run(
    experiment_id: int,
    payload: RunCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    experiment = _get_experiment_with_access(db, experiment_id, current_user)

    run = ExperimentRun(
        user_id=current_user.id,
        project_id=experiment.project_id,
        experiment_id=experiment_id,
        run_name=payload.run_name,
        config=payload.config,
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    return run


@router.get("/experiments/{experiment_id}/runs", response_model=list[RunOut])
def list_runs(
    experiment_id: int,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    experiment = _get_experiment_with_access(db, experiment_id, current_user)

    stmt = (
        select(ExperimentRun)
        .where(ExperimentRun.experiment_id == experiment_id)
        .order_by(ExperimentRun.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    return list(db.execute(stmt).scalars().all())


@router.get("/runs/{run_id}", response_model=RunOut)
def get_run(run_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return _get_run_with_access(db, run_id, current_user)


@router.patch("/runs/{run_id}", response_model=RunOut)
def update_run(run_id: int, payload: RunUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    run = _get_run_with_access(db, run_id, current_user)

    if payload.run_name is not None:
        run.run_name = payload.run_name
    if payload.status is not None:
        run.status = payload.status
    if payload.config is not None:
        run.config = payload.config
    if payload.metrics is not None:
        run.metrics = payload.metrics
    if payload.started_at is not None:
        run.started_at = payload.started_at
    if payload.finished_at is not None:
        run.finished_at = payload.finished_at

    db.commit()
    db.refresh(run)
    return run


@router.delete("/runs/{run_id}")
def delete_run(run_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    run = _get_run_with_access(db, run_id, current_user)

    db.delete(run)
    db.commit()
    return {"deleted": True, "run_id": run_id}
