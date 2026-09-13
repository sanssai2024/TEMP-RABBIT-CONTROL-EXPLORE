from copy import deepcopy

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.api.routes import ideas as ideas_routes
from app.db.database import Base
from app.main import app
from app.models.idea import Idea, IdeaStatus
from app.models.idea_note import IdeaNote
from app.models.idea_processing import IdeaProcessing
from app.services.ai_service import AIService, FakeAIProvider


VALID_RESPONSE = {
    "clean_idea": "A small planning tool for personal ideas",
    "core_question": "How can I make idea triage more actionable?",
    "branches": [
        {"title": "Workflow design", "description": "Design the triage flow", "relevance": "High"},
        {"title": "Decision support", "description": "Decide what to act on now", "relevance": "High"},
    ],
    "connections": ["personal productivity", "AI workflow design"],
    "feasibility": {
        "practical": "High",
        "technical_difficulty": "LOW",
        "knowledge_difficulty": "MEDIUM",
        "overall_complexity": "MEDIUM",
    },
    "knowledge_gaps": ["basic product design"],
    "risks": ["scope creep"],
    "assumptions": ["a single-user workflow is enough"],
    "decision": "NOW",
    "decision_reason": "It is small enough to test quickly.",
    "next_action": "Draft the first minimal version.",
    "scores": {
        "usefulness": 8,
        "feasibility": 7,
        "learning_value": 9,
        "novelty": 6,
        "effort": 4,
        "rabbit_hole_risk": 3,
    },
}


@pytest.fixture
def browser_context(monkeypatch: pytest.MonkeyPatch):
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        with Session(engine) as db:
            yield db

    def fake_ai_service() -> AIService:
        return AIService(
            provider=FakeAIProvider(response=deepcopy(VALID_RESPONSE)),
            model_name="test-model",
            api_key="test-key",
        )

    app.dependency_overrides[ideas_routes.get_db] = override_get_db
    monkeypatch.setattr(ideas_routes, "get_ai_service", fake_ai_service)

    with TestClient(app) as client:
        yield client, engine

    app.dependency_overrides.clear()
    engine.dispose()


def get_session(engine) -> Session:
    return Session(engine)


def test_browser_pages_load(browser_context) -> None:
    client, engine = browser_context
    idea = Idea(original_idea="Existing idea", status=IdeaStatus.INBOX.value)
    with get_session(engine) as db:
        db.add(idea)
        db.commit()
        db.refresh(idea)
        idea_id = idea.id

    assert client.get("/").status_code == 200
    assert client.get("/ideas/new").status_code == 200
    assert client.get("/ideas").status_code == 200
    assert client.get(f"/ideas/{idea_id}").status_code == 200


def test_control_submission_works_with_fake_ai(browser_context) -> None:
    client, engine = browser_context
    response = client.post("/ideas", data={"original_idea": "Build a small tool", "mode": "CONTROL"})

    assert response.status_code == 200
    assert "Decision" in response.text
    with get_session(engine) as db:
        processing = db.query(IdeaProcessing).one()
        assert processing.mode == "CONTROL"


def test_explore_submission_works_with_fake_ai(browser_context) -> None:
    client, engine = browser_context
    response = client.post("/ideas", data={"original_idea": "Explore a learning workflow", "mode": "EXPLORE"})

    assert response.status_code == 200
    with get_session(engine) as db:
        processing = db.query(IdeaProcessing).one()
        assert processing.mode == "EXPLORE"


def test_blank_idea_and_invalid_mode_are_rejected(browser_context) -> None:
    client, engine = browser_context
    blank_response = client.post("/ideas", data={"original_idea": "   ", "mode": "CONTROL"})
    invalid_response = client.post("/ideas", data={"original_idea": "An idea", "mode": "INVALID"})

    assert blank_response.status_code == 400
    assert "Please provide an idea" in blank_response.text
    assert invalid_response.status_code == 400
    assert "valid processing mode" in invalid_response.text
    with get_session(engine) as db:
        assert db.query(Idea).count() == 0


def test_failed_ai_keeps_raw_idea_without_successful_processing_or_decision(monkeypatch, browser_context) -> None:
    client, engine = browser_context

    class BrokenProvider:
        def process(self, *, prompt: str, model: str):
            raise TimeoutError("test provider failure")

    monkeypatch.setattr(
        ideas_routes,
        "get_ai_service",
        lambda: AIService(provider=BrokenProvider(), model_name="test-model", api_key="test-key"),
    )
    response = client.post("/ideas", data={"original_idea": "Preserve this raw idea", "mode": "CONTROL"})

    assert response.status_code == 400
    with get_session(engine) as db:
        idea = db.query(Idea).one()
        assert idea.original_idea == "Preserve this raw idea"
        assert idea.current_decision is None
        assert db.query(IdeaProcessing).count() == 0


def test_retry_reuses_existing_idea_without_duplicate(monkeypatch, browser_context) -> None:
    client, engine = browser_context

    class BrokenProvider:
        def process(self, *, prompt: str, model: str):
            raise TimeoutError("test provider failure")

    monkeypatch.setattr(
        ideas_routes,
        "get_ai_service",
        lambda: AIService(provider=BrokenProvider(), model_name="test-model", api_key="test-key"),
    )
    client.post("/ideas", data={"original_idea": "Retry this idea", "mode": "CONTROL"})

    monkeypatch.setattr(
        ideas_routes,
        "get_ai_service",
        lambda: AIService(
            provider=FakeAIProvider(response=deepcopy(VALID_RESPONSE)),
            model_name="test-model",
            api_key="test-key",
        ),
    )
    with get_session(engine) as db:
        idea_id = db.query(Idea).one().id

    retry_response = client.post(f"/ideas/{idea_id}/reprocess", data={"mode": "CONTROL"})

    assert retry_response.status_code == 200
    with get_session(engine) as db:
        assert db.query(Idea).count() == 1
        assert db.query(IdeaProcessing).count() == 1


def test_successful_processing_and_reprocessing_preserve_history(browser_context) -> None:
    client, engine = browser_context
    first_response = client.post("/ideas", data={"original_idea": "Keep processing history", "mode": "CONTROL"})
    assert first_response.status_code == 200

    with get_session(engine) as db:
        idea = db.query(Idea).one()
        idea_id = idea.id
        first = db.query(IdeaProcessing).one()
        first_payload = deepcopy(first.structured_result_json)

    second_response = client.post(f"/ideas/{idea_id}/reprocess", data={"mode": "EXPLORE"})

    assert second_response.status_code == 200
    assert "Processing History" in second_response.text
    with get_session(engine) as db:
        processings = db.query(IdeaProcessing).order_by(IdeaProcessing.id).all()
        assert len(processings) == 2
        assert processings[0].mode == "CONTROL"
        assert processings[1].mode == "EXPLORE"
        assert processings[0].structured_result_json == first_payload
        assert processings[0].next_action == VALID_RESPONSE["next_action"]
        assert VALID_RESPONSE["clean_idea"] in second_response.text


def test_notes_persist_separately_and_blank_note_is_rejected(browser_context) -> None:
    client, engine = browser_context
    client.post("/ideas", data={"original_idea": "Add a note", "mode": "CONTROL"})
    with get_session(engine) as db:
        idea_id = db.query(Idea).one().id

    valid_response = client.post(f"/ideas/{idea_id}/notes", data={"note_text": "A user-authored note"})
    blank_response = client.post(f"/ideas/{idea_id}/notes", data={"note_text": "   "})

    assert valid_response.status_code == 200
    assert blank_response.status_code == 400
    assert "A user-authored note" in valid_response.text
    with get_session(engine) as db:
        assert db.query(IdeaNote).count() == 1
        assert db.query(IdeaProcessing).count() == 1


def test_status_update_and_no_hard_delete_ui(browser_context) -> None:
    client, engine = browser_context
    client.post("/ideas", data={"original_idea": "Update status", "mode": "CONTROL"})
    with get_session(engine) as db:
        idea_id = db.query(Idea).one().id

    valid_response = client.post(f"/ideas/{idea_id}/status", data={"status": "PARKED"})
    invalid_response = client.post(f"/ideas/{idea_id}/status", data={"status": "INVALID"})
    detail_response = client.get(f"/ideas/{idea_id}")

    assert valid_response.status_code == 200
    assert invalid_response.status_code == 400
    assert "delete" not in detail_response.text.lower()
    with get_session(engine) as db:
        assert db.get(Idea, idea_id).status == "PARKED"


def test_html_is_escaped_for_raw_idea_notes_and_ai_output(monkeypatch, browser_context) -> None:
    client, engine = browser_context
    html_value = '<script>alert("x")</script>'
    response_payload = deepcopy(VALID_RESPONSE)
    response_payload["clean_idea"] = html_value
    response_payload["branches"][0]["description"] = html_value
    monkeypatch.setattr(
        ideas_routes,
        "get_ai_service",
        lambda: AIService(provider=FakeAIProvider(response=response_payload), model_name="test-model", api_key="test-key"),
    )

    response = client.post("/ideas", data={"original_idea": html_value, "mode": "CONTROL"})
    with get_session(engine) as db:
        idea_id = db.query(Idea).one().id
    note_response = client.post(f"/ideas/{idea_id}/notes", data={"note_text": html_value})

    assert "<script>" not in response.text
    assert "&lt;script&gt;" in response.text
    assert "<script>" not in note_response.text
    assert "&lt;script&gt;" in note_response.text


def test_successful_processing_commits_history_and_decision_together(browser_context) -> None:
    client, engine = browser_context
    response = client.post("/ideas", data={"original_idea": "Commit one coherent result", "mode": "CONTROL"})

    assert response.status_code == 200
    with get_session(engine) as db:
        idea = db.query(Idea).one()
        processing = db.query(IdeaProcessing).one()
        assert idea.current_decision == processing.decision == "NOW"
        assert idea.status == "ACTIVE"
