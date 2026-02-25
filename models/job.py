from datetime import date
from sqlalchemy import String, Text, Date
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[int] = mapped_column(primary_key=True)
    company: Mapped[str] = mapped_column(String(200))
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text)
    url: Mapped[str | None] = mapped_column(String(1000))
    deadline: Mapped[date | None] = mapped_column(Date)
    language: Mapped[str] = mapped_column(String(2), default="NO")  # "NO" or "EN"
    notes: Mapped[str | None] = mapped_column(Text)

    application: Mapped["Application | None"] = relationship(back_populates="job")
    research: Mapped["Research | None"] = relationship(back_populates="job")

    def __repr__(self) -> str:
        return f"<Job {self.title} @ {self.company}>"
