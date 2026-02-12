from datetime import datetime
from pydantic import BaseModel, Field


class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: str | None = None


class ProjectUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None


class ProjectOut(BaseModel):
    id: int
    user_id: int
    name: str
    description: str | None = None
    created_at: datetime
    updated_at: datetime
    role: str | None = None
    member_count: int | None = None

    class Config:
        from_attributes = True


class ProjectMemberOut(BaseModel):
    id: int
    user_id: int
    email: str
    role: str
    added_at: datetime

    class Config:
        from_attributes = True


class ProjectInviteCreate(BaseModel):
    expires_at: datetime | None = None


class ProjectInviteOut(BaseModel):
    id: int
    code: str
    created_at: datetime
    expires_at: datetime | None = None
    is_active: bool

    class Config:
        from_attributes = True


class InviteJoin(BaseModel):
    code: str = Field(..., min_length=1, max_length=20)
