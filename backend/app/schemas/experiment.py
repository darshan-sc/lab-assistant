from datetime import datetime
from pydantic import BaseModel, Field


class ExperimentCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=300)
    goal: str | None = None
    protocol: str | None = None
    paper_id: int | None = None


class ExperimentUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=300)
    goal: str | None = None
    protocol: str | None = None
    results: str | None = None
    status: str | None = None
    paper_id: int | None = None


class ExperimentOut(BaseModel):
    id: int
    user_id: int
    project_id: int | None = None
    paper_id: int | None = None
    title: str
    goal: str | None = None
    protocol: str | None = None
    results: str | None = None
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Experiment Run schemas
class RunCreate(BaseModel):
    run_name: str | None = None
    config: dict | None = None


class RunUpdate(BaseModel):
    run_name: str | None = None
    status: str | None = None
    config: dict | None = None
    metrics: dict | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None


class RunOut(BaseModel):
    id: int
    user_id: int
    project_id: int | None = None
    experiment_id: int
    run_name: str | None = None
    status: str
    config: dict | None = None
    metrics: dict | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
