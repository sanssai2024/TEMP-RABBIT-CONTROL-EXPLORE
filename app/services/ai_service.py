from __future__ import annotations

import json
import logging
import re
from typing import Protocol

import httpx

from app.models.idea import Idea
from app.models.idea_processing import IdeaProcessing, IdeaProcessingMode
from app.prompts.control_prompt import CONTROL_PROMPT
from app.prompts.explore_prompt import EXPLORE_PROMPT
from app.schemas.ai_processing import AIProcessingResult


logger = logging.getLogger(__name__)


class AIProviderError(Exception):
    pass


class AIConfigurationError(AIProviderError):
    pass


class AIProcessingValidationError(AIProviderError):
    pass


class AIProviderProtocol(Protocol):
    def process(self, *, prompt: str, model: str) -> dict:
        ...


class FakeAIProvider:
    def __init__(self, response: dict | None = None):
        self.response = response

    def process(self, *, prompt: str, model: str) -> dict:
        if self.response is None:
            raise AIProviderError("No fake provider response configured")
        return self.response


class OpenAICompatibleProvider:
    def __init__(self, api_key: str, base_url: str | None = None):
        self.api_key = api_key
        self.base_url = base_url or "https://api.openai.com/v1"

    def process(self, *, prompt: str, model: str) -> dict:
        if not self.api_key:
            raise AIConfigurationError("AI API key is missing")

        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": "Return only valid JSON matching the required TEMP_RABBIT schema."},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.2,
            "response_format": {"type": "json_object"},
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        try:
            response = httpx.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=30.0,
            )
        except httpx.HTTPError as exc:
            logger.error("AI failure layer=HTTP request error_type=%s", type(exc).__name__)
            raise AIProviderError("AI provider request failed") from exc

        if response.status_code >= 400:
            error_type, error_code, error_message = self._safe_error_details(response)
            logger.error(
                "AI failure layer=provider HTTP status=%s provider_error_type=%s provider_error_code=%s sanitized_message=%s",
                response.status_code,
                error_type,
                error_code,
                error_message,
            )
            raise AIProviderError(f"AI provider returned status {response.status_code}: {error_message}")

        try:
            provider_payload = response.json()
        except ValueError as exc:
            logger.error("AI failure layer=provider response parsing error_type=%s", type(exc).__name__)
            raise AIProcessingValidationError("AI provider returned invalid response JSON") from exc

        try:
            content = provider_payload["choices"][0]["message"]["content"]
        except (KeyError, TypeError, IndexError) as exc:
            logger.error("AI failure layer=provider response parsing error_type=%s", type(exc).__name__)
            raise AIProcessingValidationError("AI provider returned malformed structured output") from exc

        try:
            return json.loads(content)
        except (TypeError, ValueError) as exc:
            logger.error("AI failure layer=JSON decoding error_type=%s", type(exc).__name__)
            raise AIProcessingValidationError("AI provider returned invalid structured JSON") from exc

    @staticmethod
    def _safe_error_details(response: httpx.Response) -> tuple[str, str, str]:
        try:
            payload = response.json()
        except ValueError:
            payload = {}

        error = payload.get("error", {}) if isinstance(payload, dict) else {}
        if isinstance(error, dict):
            error_type = str(error.get("type") or "unknown")
            error_code = str(error.get("code") or "unknown")
            message = str(error.get("message") or "provider returned no error message")
        else:
            error_type = "unknown"
            error_code = "unknown"
            message = "provider returned an unstructured error"

        sanitized = re.sub(r"Bearer\s+\S+", "Bearer [redacted]", message, flags=re.IGNORECASE)
        sanitized = re.sub(r"\b(?:sk|key)-[A-Za-z0-9_-]+\b", "[redacted]", sanitized)
        return error_type[:100], error_code[:100], sanitized[:500]


class AIService:
    def __init__(self, provider: AIProviderProtocol, model_name: str, api_key: str | None = None):
        self.provider = provider
        self.model_name = model_name
        self.api_key = api_key

    def _require_api_key(self) -> None:
        if not self.api_key:
            raise AIConfigurationError("AI API key is missing")

    def _prompt_for_mode(self, raw_idea: str, mode: IdeaProcessingMode) -> str:
        if mode == IdeaProcessingMode.CONTROL:
            return CONTROL_PROMPT.format(raw_idea=raw_idea)
        if mode == IdeaProcessingMode.EXPLORE:
            return EXPLORE_PROMPT.format(raw_idea=raw_idea)
        raise ValueError(f"Unsupported mode: {mode}")

    def process_idea(self, raw_idea: str, mode: IdeaProcessingMode, *, context: str | None = None) -> AIProcessingResult:
        self._require_api_key()

        prompt = self._prompt_for_mode(raw_idea, mode)
        if context:
            prompt = f"{prompt}\n\nAdditional context:\n{context}"

        provider_response = self.provider.process(prompt=prompt, model=self.model_name)
        if not isinstance(provider_response, dict):
            raise AIProcessingValidationError("Provider returned malformed structured output")

        try:
            result = AIProcessingResult.model_validate(provider_response)
        except Exception as exc:  # pragma: no cover - defensive catch for validation failure
            logger.error("AI failure layer=Pydantic validation error_type=%s", type(exc).__name__)
            raise AIProcessingValidationError("AI output failed validation") from exc

        return result

    def create_processing_record(self, idea: Idea, mode: IdeaProcessingMode, result: AIProcessingResult) -> IdeaProcessing:
        return IdeaProcessing(
            idea_id=idea.id,
            mode=mode.value,
            model_name=self.model_name,
            structured_result_json=result.model_dump(mode="json"),
            decision=result.decision,
            next_action=result.next_action,
        )
