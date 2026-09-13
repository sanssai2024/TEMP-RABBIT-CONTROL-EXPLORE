from __future__ import annotations

from app.models.idea import Idea
from app.repositories.idea_repository import IdeaRepositoryProtocol
from app.schemas.idea import IdeaCreate


class IdeaService:
    def __init__(self, repository: IdeaRepositoryProtocol):
        self.repository = repository

    def create_idea(self, payload: IdeaCreate) -> Idea:
        idea = Idea(
            original_idea=payload.original_idea,
            status=payload.status.value,
            current_decision=payload.current_decision.value if payload.current_decision else None,
        )
        return self.repository.create(idea)
