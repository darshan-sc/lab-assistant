from typing import Optional
from pydantic import BaseModel

class ExperimentBase(BaseModel):
    title: str
    description: Optional[str] = None
    status: str = "planned"
    paper_id: Optional[int] = None

class ExperimentCreate(ExperimentBase):
    pass

class ExperimentUpdate(ExperimentBase):
    pass

class Experiment(ExperimentBase):
    id: int
    user_id: int

    class Config:
        from_attributes = True
