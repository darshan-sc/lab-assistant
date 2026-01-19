from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey, Text, DateTime, func
from .base import Base

class Note(Base):
    __tablename__ = "notes"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)
    project_id: Mapped[int | None] = mapped_column(ForeignKey("projects.id"), index=True)

    # optional links (a note can belong to a paper OR an experiment OR run)
    paper_id: Mapped[int | None] = mapped_column(ForeignKey("papers.id"), index=True)
    experiment_id: Mapped[int | None] = mapped_column(ForeignKey("experiments.id"), index=True)
    experiment_run_id: Mapped[int | None] = mapped_column(ForeignKey("experiment_runs.id"), index=True)

    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="notes")
    project = relationship("Project", back_populates="notes")
    paper = relationship("Paper", back_populates="notes")
    experiment = relationship("Experiment", back_populates="notes")
    experiment_run = relationship("ExperimentRun", back_populates="notes")
