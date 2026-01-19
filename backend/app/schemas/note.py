from typing import Optional
from datetime import datetime
from pydantic import BaseModel

class NoteBase(BaseModel):
    content: str
    experiment_id: Optional[int] = None
    paper_id: Optional[int] = None

class NoteCreate(NoteBase):
    pass

class NoteUpdate(NoteBase):
    pass

class Note(NoteBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True
