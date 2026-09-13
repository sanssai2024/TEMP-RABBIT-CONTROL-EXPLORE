import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.database import Base
from app.models.idea import Idea, IdeaDecision, IdeaStatus
from app.models.idea_processing import IdeaProcessing, IdeaProcessingMode
from app.models.idea_note import IdeaNote


@pytest.fixture
def session() -> Session:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    with Session(engine) as db:
        yield db


def test_idea_can_be_created_and_retrieved(session: Session) -> None:
    idea = Idea(original_idea="Build a personal idea triage notebook.", status=IdeaStatus.INBOX.value)
    session.add(idea)
    session.commit()
    session.refresh(idea)

    stored = session.get(Idea, idea.id)
    assert stored is not None
    assert stored.original_idea == "Build a personal idea triage notebook."
    assert stored.status == IdeaStatus.INBOX.value


def test_idea_can_have_multiple_processing_runs(session: Session) -> None:
    idea = Idea(original_idea="Investigate a better meeting note system.", status=IdeaStatus.ACTIVE.value)
    session.add(idea)
    session.commit()

    first = IdeaProcessing(
        idea_id=idea.id,
        mode=IdeaProcessingMode.CONTROL.value,
        model_name="test-model",
        structured_result_json={"clean_idea": "Better meeting notes"},
        decision=IdeaDecision.NOW.value,
        next_action="Test the workflow",
    )
    second = IdeaProcessing(
        idea_id=idea.id,
        mode=IdeaProcessingMode.EXPLORE.value,
        model_name="test-model-2",
        structured_result_json={"core_question": "Which workflows matter most?"},
        decision=IdeaDecision.LATER.value,
        next_action="Map related concepts",
    )

    session.add_all([first, second])
    session.commit()

    processings = session.query(IdeaProcessing).filter_by(idea_id=idea.id).all()
    assert len(processings) == 2
    assert processings[0].mode == IdeaProcessingMode.CONTROL.value
    assert processings[1].mode == IdeaProcessingMode.EXPLORE.value


def test_notes_belong_to_the_correct_idea(session: Session) -> None:
    idea = Idea(original_idea="Create a small AI journaling workflow.", status=IdeaStatus.PARKED.value)
    session.add(idea)
    session.commit()

    note_a = IdeaNote(idea_id=idea.id, note_text="This could be useful for weekly planning.")
    note_b = IdeaNote(idea_id=idea.id, note_text="Need to keep the scope small.")
    session.add_all([note_a, note_b])
    session.commit()

    notes = session.query(IdeaNote).filter_by(idea_id=idea.id).all()
    assert len(notes) == 2
    assert {note.note_text for note in notes} == {
        "This could be useful for weekly planning.",
        "Need to keep the scope small.",
    }


def test_invalid_processing_mode_and_blank_note_are_rejected() -> None:
    with pytest.raises(ValueError):
        IdeaProcessingMode("UNKNOWN")

    with pytest.raises(ValueError):
        IdeaNote(idea_id=1, note_text="   ")
