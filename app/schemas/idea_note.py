from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class IdeaNoteBase(BaseModel):
    note_text: str = Field(..., min_length=1, max_length=5000)

    @field_validator("note_text")
    @classmethod
    def validate_note_text(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("note_text cannot be blank")
        return cleaned


class IdeaNoteCreate(IdeaNoteBase):
    idea_id: int


class IdeaNoteRead(IdeaNoteBase):
    id: int
    idea_id: int
    created_at: datetime

    model_config = {"from_attributes": True}
