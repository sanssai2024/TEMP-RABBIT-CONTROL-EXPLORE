from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from app.db.database import Base


class IdeaNote(Base):
    __tablename__ = "idea_notes"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    idea_id: Mapped[int] = mapped_column(ForeignKey("ideas.id", ondelete="CASCADE"), nullable=False, index=True)
    note_text: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc), nullable=False)

    idea: Mapped["Idea"] = relationship(back_populates="notes")

    @validates("note_text")
    def validate_note_text(self, key: str, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("note_text cannot be blank")
        return cleaned

    def __repr__(self) -> str:
        return f"IdeaNote(id={self.id}, idea_id={self.idea_id})"
