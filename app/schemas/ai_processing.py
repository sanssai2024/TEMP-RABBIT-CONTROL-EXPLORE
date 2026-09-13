from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator


class BranchResult(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1, max_length=2000)
    relevance: str = Field(..., min_length=1, max_length=500)

    @field_validator("title", "description", "relevance")
    @classmethod
    def validate_non_blank(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("value cannot be blank")
        return cleaned


class FeasibilityResult(BaseModel):
    practical: str = Field(..., min_length=1, max_length=200)
    technical_difficulty: Literal["LOW", "MEDIUM", "HIGH"]
    knowledge_difficulty: Literal["LOW", "MEDIUM", "HIGH"]
    overall_complexity: Literal["LOW", "MEDIUM", "HIGH"]

    @field_validator("practical")
    @classmethod
    def validate_practical(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("practical cannot be blank")
        return cleaned


class ScoreResult(BaseModel):
    usefulness: int = Field(..., ge=1, le=10)
    feasibility: int = Field(..., ge=1, le=10)
    learning_value: int = Field(..., ge=1, le=10)
    novelty: int = Field(..., ge=1, le=10)
    effort: int = Field(..., ge=1, le=10)
    rabbit_hole_risk: int = Field(..., ge=1, le=10)


class AIProcessingResult(BaseModel):
    clean_idea: str = Field(..., min_length=1, max_length=2000)
    core_question: str = Field(..., min_length=1, max_length=2000)
    branches: list[BranchResult] = Field(..., min_length=1)
    connections: list[str] = Field(default_factory=list)
    feasibility: FeasibilityResult
    knowledge_gaps: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    decision: Literal["NOW", "LATER", "PARK"]
    decision_reason: str = Field(..., min_length=1, max_length=2000)
    next_action: str = Field(..., min_length=1, max_length=500)
    scores: ScoreResult

    @field_validator("clean_idea", "core_question", "decision_reason", "next_action")
    @classmethod
    def validate_required_strings(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("required field cannot be blank")
        return cleaned

    @field_validator("connections", "knowledge_gaps", "risks", "assumptions")
    @classmethod
    def validate_string_lists(cls, value: list[str]) -> list[str]:
        cleaned_list = []
        for item in value:
            cleaned = str(item).strip()
            if not cleaned:
                raise ValueError("list entries cannot be blank")
            cleaned_list.append(cleaned)
        return cleaned_list
