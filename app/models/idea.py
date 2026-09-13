from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class IdeaStatus(str, Enum):
    INBOX = "INBOX"
    PROCESSING = "PROCESSING"
    ACTIVE = "ACTIVE"
    EXPLORING = "EXPLORING"
    PARKED = "PARKED"
    COMPLETED = "COMPLETED"
    DEAD = "DEAD"


class IdeaDecision(str, Enum):
    NOW = "NOW"
    LATER = "LATER"
    PARK = "PARK"


class Idea(Base):
    __tablename__ = "ideas"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    original_idea: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default=IdeaStatus.INBOX.value, nullable=False)
    current_decision: Mapped[str | None] = mapped_column(String(32), nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    processings: Mapped[list["IdeaProcessing"]] = relationship(
        back_populates="idea",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    notes: Mapped[list["IdeaNote"]] = relationship(
        back_populates="idea",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    def __repr__(self) -> str:
        return f"Idea(id={self.id}, status={self.status}, decision={self.current_decision})"
