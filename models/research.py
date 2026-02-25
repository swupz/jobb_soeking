from datetime import datetime
from sqlalchemy import String, Text, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base


class Research(Base):
    __tablename__ = "research"

    id: Mapped[int] = mapped_column(primary_key=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("jobs.id"), unique=True)
    scraped_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    # Raw scraped content per source
    company_website: Mapped[str | None] = mapped_column(Text)
    glassdoor: Mapped[str | None] = mapped_column(Text)
    news: Mapped[str | None] = mapped_column(Text)
    linkedin: Mapped[str | None] = mapped_column(Text)

    # AI-generated summary of all research, used as context for generation
    summary: Mapped[str | None] = mapped_column(Text)

    job: Mapped["Job"] = relationship(back_populates="research")
