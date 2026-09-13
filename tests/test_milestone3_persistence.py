import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.database import Base
from app.models.idea import IdeaDecision, IdeaStatus
from app.models.idea_processing import IdeaProcessingMode
from app.services.idea_persistence_service import IdeaPersistenceService


@pytest.fixture
def db_session() -> Session:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    with Session(engine) as db:
        yield db


def test_valid_idea_can_be_created_and_retrieved(db_session: Session) -> None:
    service = IdeaPersistenceService(db_session)
    idea = service.create_idea("Build a tiny personal idea tracker.")

    stored = service.get_idea(idea.id)
    assert stored.original_idea == "Build a tiny personal idea tracker."
    assert stored.status == IdeaStatus.INBOX.value
    assert stored.current_decision is None


def test_multiple_ideas_can_be_listed(db_session: Session) -> None:
    service = IdeaPersistenceService(db_session)
    service.create_idea("Idea A")
    service.create_idea("Idea B")

    ideas = service.list_ideas()
    assert len(ideas) == 2
    assert {idea.original_idea for idea in ideas} == {"Idea A", "Idea B"}


def test_one_idea_can_have_multiple_processing_runs(db_session: Session) -> None:
    service = IdeaPersistenceService(db_session)
    idea = service.create_idea("Investigate a better weekly review workflow.", status=IdeaStatus.ACTIVE)

    first = service.add_processing(
        idea.id,
        mode=IdeaProcessingMode.CONTROL,
        model_name="model-a",
        structured_result_json={"clean_idea": "Weekly review workflow"},
        decision=IdeaDecision.NOW,
        next_action="Draft the first version",
    )
    second = service.add_processing(
        idea.id,
        mode=IdeaProcessingMode.EXPLORE,
        model_name="model-b",
        structured_result_json={"core_question": "What should the first feature be?"},
        decision=IdeaDecision.LATER,
        next_action="Identify follow-up questions",
    )

    processings = service.list_processings_for_idea(idea.id)
    assert len(processings) == 2
    assert processings[0].id == first.id
    assert processings[1].id == second.id
    assert processings[0].mode == IdeaProcessingMode.CONTROL.value
    assert processings[1].mode == IdeaProcessingMode.EXPLORE.value
    assert processings[0].next_action == "Draft the first version"
    assert processings[1].structured_result_json["core_question"] == "What should the first feature be?"


def test_multiple_notes_can_belong_to_one_idea(db_session: Session) -> None:
    service = IdeaPersistenceService(db_session)
    idea = service.create_idea("Create a minimal weekly goal tracker.")

    service.add_note(idea.id, "Keep it simple.")
    service.add_note(idea.id, "Focus on one decision per week.")

    notes = service.list_notes_for_idea(idea.id)
    assert len(notes) == 2
    assert [note.note_text for note in notes] == ["Keep it simple.", "Focus on one decision per week."]


def test_invalid_idea_id_and_blank_note_fail_safely(db_session: Session) -> None:
    service = IdeaPersistenceService(db_session)

    with pytest.raises(ValueError):
        service.get_idea(999)

    with pytest.raises(ValueError):
        service.add_note(1, "   ")


def test_invalid_processing_mode_is_rejected(db_session: Session) -> None:
    service = IdeaPersistenceService(db_session)
    idea = service.create_idea("Idea for testing invalid process mode.")

    with pytest.raises(ValueError):
        service.add_processing(
            idea.id,
            mode="INVALID_MODE",
            model_name="m",
            structured_result_json={},
            decision=IdeaDecision.NOW,
            next_action="No-op",
        )
