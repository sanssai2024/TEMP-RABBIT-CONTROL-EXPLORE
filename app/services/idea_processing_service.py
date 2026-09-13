from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.idea import Idea, IdeaDecision, IdeaStatus
from app.models.idea_processing import IdeaProcessing, IdeaProcessingMode
from app.repositories.idea_processing_repository import SQLAlchemyIdeaProcessingRepository
from app.services.ai_service import AIProcessingValidationError, AIService


class IdeaProcessingService:
    def __init__(self, db: Session, ai_service: AIService):
        self.db = db
        self.ai_service = ai_service
        self.processing_repository = SQLAlchemyIdeaProcessingRepository(db)

    def process_idea(self, idea: Idea, mode: IdeaProcessingMode, *, context: str | None = None) -> IdeaProcessing:
        result = self.ai_service.process_idea(idea.original_idea, mode, context=context)

        if not result.next_action.strip():
            raise AIProcessingValidationError("next_action cannot be blank")

        processing = self.ai_service.create_processing_record(idea, mode, result)
        persisted = self.processing_repository.create(processing)

        if result.decision in {"NOW", "LATER", "PARK"}:
            idea.current_decision = result.decision
            idea.status = IdeaStatus.ACTIVE.value if result.decision == "NOW" else IdeaStatus.PARKED.value if result.decision == "PARK" else IdeaStatus.EXPLORING.value
            self.db.add(idea)
        self.db.commit()
        self.db.refresh(persisted)

        return persisted
