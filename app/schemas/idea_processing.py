from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator

from app.models.idea import IdeaDecision
from app.models.idea_processing import IdeaProcessingMode


class IdeaProcessingBase(BaseModel):
    mode: IdeaProcessingMode
    model_name: str | None = Field(default=None, max_length=128)
    structured_result_json: dict[str, Any] = Field(default_factory=dict)
    decision: IdeaDecision | None = None
    next_action: str | None = Field(default=None, max_length=500)


class IdeaProcessingCreate(IdeaProcessingBase):
    idea_id: int


class IdeaProcessingRead(IdeaProcessingBase):
    id: int
    idea_id: int
    processed_at: datetime

    model_config = {"from_attributes": True}


class IdeaProcessingUpdate(BaseModel):
    mode: IdeaProcessingMode | None = None
    model_name: str | None = Field(default=None, max_length=128)
    structured_result_json: dict[str, Any] | None = None
    decision: IdeaDecision | None = None
    next_action: str | None = Field(default=None, max_length=500)

    @field_validator("next_action")
    @classmethod
    def validate_next_action(cls, value: str | None) -> str | None:
        if value is None:
            return value
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("next_action cannot be blank")
        return cleaned
