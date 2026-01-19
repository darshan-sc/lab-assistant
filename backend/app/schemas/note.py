from datetime import datetime
from pydantic import BaseModel


class NoteCreate(BaseModel):
    content: str
    project_id: int | None = None
    paper_id: int | None = None
    experiment_id: int | None = None
    experiment_run_id: int | None = None


class NoteUpdate(BaseModel):
    content: str | None = None


class NoteOut(BaseModel):
    id: int
    user_id: int
    project_id: int | None = None
    paper_id: int | None = None
    experiment_id: int | None = None
    experiment_run_id: int | None = None
    content: str
    created_at: datetime

    class Config:
        from_attributes = True
