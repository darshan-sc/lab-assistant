from pydantic import BaseModel, Field


class PaperUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=500)
    abstract: str | None = None


class PaperOut(BaseModel):
    id: int
    user_id: int
    title: str | None = None
    abstract: str | None = None
    pdf_path: str | None = None

    class Config:
        from_attributes = True
