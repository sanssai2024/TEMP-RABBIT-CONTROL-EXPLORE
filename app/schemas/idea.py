from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.models.idea import IdeaDecision, IdeaStatus


class IdeaBase(BaseModel):
    original_idea: str = Field(..., min_length=1, max_length=5000)
    status: IdeaStatus = IdeaStatus.INBOX
    current_decision: IdeaDecision | None = None

    @field_validator("original_idea")
    @classmethod
    def validate_original_idea(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("original_idea cannot be blank")
        return cleaned


class IdeaCreate(IdeaBase):
    pass


class IdeaRead(IdeaBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class IdeaUpdate(BaseModel):
    status: IdeaStatus | None = None
    current_decision: IdeaDecision | None = None
    original_idea: str | None = Field(default=None, min_length=1, max_length=5000)

    @field_validator("original_idea")
    @classmethod
    def validate_original_idea(cls, value: str | None) -> str | None:
        if value is None:
            return value
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("original_idea cannot be blank")
        return cleaned
