from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.idea import Idea, IdeaDecision, IdeaStatus
from app.models.idea_note import IdeaNote
from app.models.idea_processing import IdeaProcessing, IdeaProcessingMode
from app.repositories.idea_note_repository import SQLAlchemyIdeaNoteRepository
from app.repositories.idea_processing_repository import SQLAlchemyIdeaProcessingRepository
from app.repositories.idea_repository import SQLAlchemyIdeaRepository


class IdeaPersistenceService:
    def __init__(self, db: Session):
        self.db = db
        self.idea_repository = SQLAlchemyIdeaRepository(db)
        self.processing_repository = SQLAlchemyIdeaProcessingRepository(db)
        self.note_repository = SQLAlchemyIdeaNoteRepository(db)

    def create_idea(self, original_idea: str, status: str | IdeaStatus = IdeaStatus.INBOX, current_decision: str | IdeaDecision | None = None) -> Idea:
        cleaned = original_idea.strip()
        if not cleaned:
            raise ValueError("original_idea cannot be blank")

        if isinstance(status, IdeaStatus):
            status_value = status.value
        else:
            status_value = IdeaStatus(status).value

        if current_decision is not None:
            decision_value = current_decision.value if isinstance(current_decision, IdeaDecision) else IdeaDecision(current_decision).value
        else:
            decision_value = None

        idea = Idea(original_idea=cleaned, status=status_value, current_decision=decision_value)
        return self.idea_repository.create(idea)

    def get_idea(self, idea_id: int) -> Idea:
        idea = self.db.get(Idea, idea_id)
        if idea is None:
            raise ValueError(f"Idea with id={idea_id} not found")
        return idea

    def list_ideas(self) -> list[Idea]:
        return self.db.query(Idea).order_by(Idea.created_at.desc()).all()

    def add_processing(self, idea_id: int, mode: str | IdeaProcessingMode, model_name: str | None, structured_result_json: dict, decision: str | IdeaDecision | None, next_action: str | None) -> IdeaProcessing:
        self.get_idea(idea_id)

        if isinstance(mode, IdeaProcessingMode):
            mode_value = mode.value
        else:
            mode_value = IdeaProcessingMode(mode).value

        decision_value = None
        if decision is not None:
            decision_value = decision.value if isinstance(decision, IdeaDecision) else IdeaDecision(decision).value

        processing = IdeaProcessing(
            idea_id=idea_id,
            mode=mode_value,
            model_name=model_name,
            structured_result_json=structured_result_json,
            decision=decision_value,
            next_action=next_action,
        )
        return self.processing_repository.create(processing)

    def list_processings_for_idea(self, idea_id: int) -> list[IdeaProcessing]:
        self.get_idea(idea_id)
        return self.processing_repository.list_for_idea(idea_id)

    def add_note(self, idea_id: int, note_text: str) -> IdeaNote:
        self.get_idea(idea_id)
        cleaned = note_text.strip()
        if not cleaned:
            raise ValueError("note_text cannot be blank")

        note = IdeaNote(idea_id=idea_id, note_text=cleaned)
        return self.note_repository.create(note)

    def list_notes_for_idea(self, idea_id: int) -> list[IdeaNote]:
        self.get_idea(idea_id)
        return self.note_repository.list_for_idea(idea_id)
