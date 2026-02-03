import enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, ForeignKey, Text, DateTime, func, JSON
# from sqlalchemy.dialects.postgresql import JSONB
from .base import Base


class RunStatus(str, enum.Enum):
    PLANNED = "planned"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"


class ExperimentRun(Base):
    """Individual run within an experiment group."""
    __tablename__ = "experiment_runs"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)
    project_id: Mapped[int | None] = mapped_column(ForeignKey("projects.id"), index=True)
    experiment_id: Mapped[int] = mapped_column(ForeignKey("experiments.id"), index=True, nullable=False)

    run_name: Mapped[str | None] = mapped_column(String(200))  # e.g., "seed=42", "sweep_003"
    status: Mapped[str] = mapped_column(String(20), default=RunStatus.PLANNED.value)

    # Flexible structured data for ML experiments
    config: Mapped[dict | None] = mapped_column(JSON)  # model/dataset/hyperparams/seed/commit/command
    metrics: Mapped[dict | None] = mapped_column(JSON)  # acc/loss/f1/runtime/etc

    started_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    user = relationship("User")
    project = relationship("Project")
    experiment = relationship("Experiment", back_populates="runs")
    notes = relationship("Note", back_populates="experiment_run", cascade="all, delete-orphan")
