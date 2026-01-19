import enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, ForeignKey, Text, DateTime, Integer, func
from pgvector.sqlalchemy import Vector
from .base import Base


class ChunkSource(str, enum.Enum):
    PAPER = "paper"
    NOTE = "note"
    EXPERIMENT = "experiment"


class Chunk(Base):
    __tablename__ = "chunks"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)

    # Source tracking - which entity this chunk came from
    source_type: Mapped[str] = mapped_column(String(20), nullable=False)  # paper, note, experiment
    paper_id: Mapped[int | None] = mapped_column(ForeignKey("papers.id", ondelete="CASCADE"), index=True)
    note_id: Mapped[int | None] = mapped_column(ForeignKey("notes.id", ondelete="CASCADE"), index=True)
    experiment_id: Mapped[int | None] = mapped_column(ForeignKey("experiments.id", ondelete="CASCADE"), index=True)

    # Chunk content and position
    content: Mapped[str] = mapped_column(Text, nullable=False)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)  # Position in source

    # Vector embedding (OpenAI text-embedding-3-small = 1536 dimensions)
    embedding = mapped_column(Vector(1536))

    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User")
    paper = relationship("Paper")
    note = relationship("Note")
    experiment = relationship("Experiment")
