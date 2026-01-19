import enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, ForeignKey, Text, DateTime, Integer, func
from .base import Base


class ProcessingStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class Paper(Base):
    __tablename__ = "papers"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)

    title: Mapped[str] = mapped_column(String(500), nullable=False)
    abstract: Mapped[str | None] = mapped_column(Text)
    pdf_path: Mapped[str | None] = mapped_column(String(1024))
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Processing fields
    processing_status: Mapped[str] = mapped_column(
        String(20), default=ProcessingStatus.PENDING.value, index=True
    )
    extracted_text: Mapped[str | None] = mapped_column(Text)
    processing_error: Mapped[str | None] = mapped_column(Text)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    processing_started_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True))
    processing_completed_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True))

    user = relationship("User", back_populates="papers")
    notes = relationship("Note", back_populates="paper", cascade="all, delete-orphan")
