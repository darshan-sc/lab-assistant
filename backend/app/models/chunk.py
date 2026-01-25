import enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, ForeignKey, Text, DateTime, Integer, func
from pgvector.sqlalchemy import Vector
from .base import Base


class ChunkSource(str, enum.Enum):
    PAPER = "paper"
    NOTE = "note"
    EXPERIMENT = "experiment"
    RUN = "run"


class Chunk(Base):
    __tablename__ = "chunks"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)
    project_id: Mapped[int | None] = mapped_column(ForeignKey("projects.id"), index=True)

    # Source tracking - which entity this chunk came from
    source_type: Mapped[str] = mapped_column(String(20), nullable=False)  # paper, note, experiment, run
    source_id: Mapped[int] = mapped_column(Integer, nullable=False)  # ID of the source entity
    paper_id: Mapped[int | None] = mapped_column(ForeignKey("papers.id", ondelete="CASCADE"), index=True)
    note_id: Mapped[int | None] = mapped_column(ForeignKey("notes.id", ondelete="CASCADE"), index=True)
    experiment_id: Mapped[int | None] = mapped_column(ForeignKey("experiments.id", ondelete="CASCADE"), index=True)
    experiment_run_id: Mapped[int | None] = mapped_column(ForeignKey("experiment_runs.id", ondelete="CASCADE"), index=True)

    # Chunk content and position
    content: Mapped[str] = mapped_column(Text, nullable=False)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)  # Position in source

    # Page tracking
    page_start: Mapped[int | None] = mapped_column(Integer)  # First page of chunk
    page_end: Mapped[int | None] = mapped_column(Integer)  # Last page of chunk

    # Section/structure tracking
    section_title: Mapped[str | None] = mapped_column(String(200))  # e.g., "Methods", "Results"

    # Document metadata (denormalized for fast retrieval)
    doc_title: Mapped[str | None] = mapped_column(String(500))  # Paper title
    doc_authors: Mapped[str | None] = mapped_column(Text)  # Authors (comma-separated)
    doc_year: Mapped[int | None] = mapped_column(Integer)  # Publication year

    # Vector embedding (OpenAI text-embedding-3-small = 1536 dimensions)
    embedding = mapped_column(Vector(1536))

    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User")
    project = relationship("Project", back_populates="chunks")
    paper = relationship("Paper")
    note = relationship("Note")
    experiment = relationship("Experiment")
    experiment_run = relationship("ExperimentRun")
