from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, ForeignKey, Text, DateTime, UniqueConstraint, func
from .base import Base


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        UniqueConstraint("user_id", "name", name="uq_user_project_name"),
    )

    user = relationship("User", back_populates="projects")
    papers = relationship("Paper", back_populates="project")
    notes = relationship("Note", back_populates="project")
    experiments = relationship("Experiment", back_populates="project")
    chunks = relationship("Chunk", back_populates="project")
    members = relationship("ProjectMember", back_populates="project", cascade="all, delete-orphan")
    invites = relationship("ProjectInvite", back_populates="project", cascade="all, delete-orphan")
