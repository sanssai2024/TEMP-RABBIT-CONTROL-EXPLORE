from __future__ import annotations

from typing import Protocol

from sqlalchemy.orm import Session

from app.models.idea import Idea


class IdeaRepositoryProtocol(Protocol):
    def create(self, idea: Idea) -> Idea:
        ...


class SQLAlchemyIdeaRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, idea: Idea) -> Idea:
        self.db.add(idea)
        self.db.commit()
        self.db.refresh(idea)
        return idea
