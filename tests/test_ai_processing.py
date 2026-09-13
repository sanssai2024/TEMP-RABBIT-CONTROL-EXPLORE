import pytest

from app.models.idea import Idea, IdeaDecision, IdeaStatus
from app.models.idea_processing import IdeaProcessingMode
from app.schemas.ai_processing import AIProcessingResult
from app.services.ai_service import AIConfigurationError, AIProcessingValidationError, AIService, FakeAIProvider


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


def test_control_result_validates_and_selects_mode() -> None:
    service = AIService(provider=FakeAIProvider(response=VALID_RESPONSE), model_name="test-model", api_key="abc")
    result = service.process_idea("Build a minimal personal idea tracker.", IdeaProcessingMode.CONTROL)

    assert isinstance(result, AIProcessingResult)
    assert result.decision in {"NOW", "LATER", "PARK"}
    assert result.next_action
    assert result.clean_idea


def test_explore_result_validates_and_supports_multiple_branches() -> None:
    service = AIService(provider=FakeAIProvider(response=VALID_RESPONSE), model_name="test-model", api_key="abc")
    result = service.process_idea("Build a minimal personal idea tracker.", IdeaProcessingMode.EXPLORE)

    assert len(result.branches) >= 2
    assert result.connections
    assert result.core_question


def test_missing_api_key_is_rejected() -> None:
    service = AIService(provider=FakeAIProvider(response=VALID_RESPONSE), model_name="test-model", api_key="")

    with pytest.raises(AIConfigurationError):
        service.process_idea("Test idea", IdeaProcessingMode.CONTROL)


def test_missing_clean_idea_is_rejected() -> None:
    bad_response = {**VALID_RESPONSE, "clean_idea": ""}
    service = AIService(provider=FakeAIProvider(response=bad_response), model_name="test-model", api_key="abc")

    with pytest.raises(AIProcessingValidationError):
        service.process_idea("Test idea", IdeaProcessingMode.CONTROL)


def test_invalid_decision_is_rejected() -> None:
    bad_response = {**VALID_RESPONSE, "decision": "INVALID"}
    service = AIService(provider=FakeAIProvider(response=bad_response), model_name="test-model", api_key="abc")

    with pytest.raises(AIProcessingValidationError):
        service.process_idea("Test idea", IdeaProcessingMode.CONTROL)


def test_score_out_of_range_is_rejected() -> None:
    bad_response = {**VALID_RESPONSE, "scores": {**VALID_RESPONSE["scores"], "usefulness": 0}}
    service = AIService(provider=FakeAIProvider(response=bad_response), model_name="test-model", api_key="abc")

    with pytest.raises(AIProcessingValidationError):
        service.process_idea("Test idea", IdeaProcessingMode.CONTROL)


def test_blank_next_action_is_rejected() -> None:
    bad_response = {**VALID_RESPONSE, "next_action": "   "}
    service = AIService(provider=FakeAIProvider(response=bad_response), model_name="test-model", api_key="abc")

    with pytest.raises(AIProcessingValidationError):
        service.process_idea("Test idea", IdeaProcessingMode.CONTROL)


def test_provider_failure_is_handled() -> None:
    class BrokenProvider:
        def process(self, *, prompt: str, model: str):
            raise TimeoutError("timed out")

    service = AIService(provider=BrokenProvider(), model_name="test-model", api_key="abc")

    with pytest.raises(Exception):
        service.process_idea("Test idea", IdeaProcessingMode.CONTROL)
