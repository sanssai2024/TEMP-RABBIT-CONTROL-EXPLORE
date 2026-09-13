from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum

from sqlalchemy import JSON, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from app.db.database import Base


class IdeaProcessingMode(str, Enum):
    CONTROL = "CONTROL"
    EXPLORE = "EXPLORE"


class IdeaProcessing(Base):
    __tablename__ = "idea_processings"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    idea_id: Mapped[int] = mapped_column(ForeignKey("ideas.id", ondelete="CASCADE"), nullable=False, index=True)
    mode: Mapped[str] = mapped_column(String(32), nullable=False)
    model_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    structured_result_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    decision: Mapped[str | None] = mapped_column(String(32), nullable=True)
    next_action: Mapped[str | None] = mapped_column(String(500), nullable=True)
    processed_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc), nullable=False)

    idea: Mapped["Idea"] = relationship(back_populates="processings")

    @validates("mode")
    def validate_mode(self, key: str, value: str) -> str:
        return IdeaProcessingMode(value).value

    def __repr__(self) -> str:
        return f"IdeaProcessing(id={self.id}, mode={self.mode}, idea_id={self.idea_id})"
