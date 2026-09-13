import pytest
from pydantic import ValidationError

from app.models.idea import Idea, IdeaDecision, IdeaStatus
from app.schemas.idea import IdeaCreate
from app.services.idea_service import IdeaService


class DummyRepository:
    def __init__(self):
        self.items = []

    def create(self, idea):
        self.items.append(idea)
        idea.id = len(self.items)
        return idea


def test_idea_create_schema_accepts_valid_data() -> None:
    payload = IdeaCreate(
        original_idea="Build a lightweight idea triage app for personal knowledge work.",
        status=IdeaStatus.INBOX,
        current_decision=IdeaDecision.LATER,
    )

    assert payload.original_idea == "Build a lightweight idea triage app for personal knowledge work."
    assert payload.status == IdeaStatus.INBOX
    assert payload.current_decision == IdeaDecision.LATER


def test_idea_create_schema_rejects_blank_idea() -> None:
    with pytest.raises(ValidationError):
        IdeaCreate(original_idea="   ")


def test_idea_service_creates_domain_model() -> None:
    service = IdeaService(repository=DummyRepository())
    idea = service.create_idea(
        IdeaCreate(
            original_idea="Turn my notes into a searchable personal idea index.",
            status=IdeaStatus.ACTIVE,
            current_decision=IdeaDecision.NOW,
        )
    )

    assert isinstance(idea, Idea)
    assert idea.original_idea == "Turn my notes into a searchable personal idea index."
    assert idea.status == IdeaStatus.ACTIVE
    assert idea.current_decision == IdeaDecision.NOW


def test_idea_status_enum_has_expected_values() -> None:
    assert list(IdeaStatus) == [
        IdeaStatus.INBOX,
        IdeaStatus.PROCESSING,
        IdeaStatus.ACTIVE,
        IdeaStatus.EXPLORING,
        IdeaStatus.PARKED,
        IdeaStatus.COMPLETED,
        IdeaStatus.DEAD,
    ]
