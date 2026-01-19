import enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, ForeignKey, Text, DateTime, func
from .base import Base


class ExperimentStatus(str, enum.Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"


class Experiment(Base):
    """Experiment group - contains multiple runs."""
    __tablename__ = "experiments"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)
    project_id: Mapped[int | None] = mapped_column(ForeignKey("projects.id"), index=True)
    paper_id: Mapped[int | None] = mapped_column(ForeignKey("papers.id"), index=True)  # primary reference paper

    title: Mapped[str] = mapped_column(String(300), nullable=False)
    goal: Mapped[str | None] = mapped_column(Text)
    protocol: Mapped[str | None] = mapped_column(Text)  # approach plan
    results: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), default=ExperimentStatus.ACTIVE.value)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    user = relationship("User", back_populates="experiments")
    project = relationship("Project", back_populates="experiments")
    paper = relationship("Paper")
    notes = relationship("Note", back_populates="experiment", cascade="all, delete-orphan")
    runs = relationship("ExperimentRun", back_populates="experiment", cascade="all, delete-orphan")
