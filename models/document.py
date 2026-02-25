from datetime import datetime
from sqlalchemy import String, Text, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base

DOCUMENT_TYPES = ["cv", "cover_letter"]


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(primary_key=True)
    application_id: Mapped[int] = mapped_column(ForeignKey("applications.id"))
    type: Mapped[str] = mapped_column(String(20))       # "cv" or "cover_letter"
    language: Mapped[str] = mapped_column(String(2))    # "NO" or "EN"
    markdown_content: Mapped[str] = mapped_column(Text)
    pdf_path: Mapped[str | None] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    application: Mapped["Application"] = relationship(back_populates="documents")
