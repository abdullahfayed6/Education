from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


Preference = Literal["abroad", "egypt", "remote", "hybrid"]


class UserInput(BaseModel):
    academic_year: int = Field(ge=1, le=5)
    preference: Preference
    track: str
    skills: list[str]
    notes: str | None = None


class TaskSimulationInput(BaseModel):
    company_name: str = Field(min_length=1)
    task_title: str = Field(min_length=1)


class TaskSimulationOutput(BaseModel):
    company_name: str
    task_title: str
    simulation: str


class SkillBuckets(BaseModel):
    hard: list[str] = Field(default_factory=list)
    tools: list[str] = Field(default_factory=list)
    soft: list[str] = Field(default_factory=list)


class UserProfile(BaseModel):
    year_level: str
    track: str
    location_preference: Preference
    skills: SkillBuckets
    seniority_target: str


class QuerySpec(BaseModel):
    query: str
    provider: str
    rationale: str


class OpportunityRaw(BaseModel):
    title: str
    company: str
    location: str
    url: str
    snippet: str | None = None
    source: str
    posted_date: str | None = None


class OpportunityClean(BaseModel):
    title: str
    company: str
    location: str
    url: str
    source: str
    description: str
    work_type: str | None = None
    posted_date: str | None = None


class OpportunityScore(BaseModel):
    title: str
    company: str
    location: str
    url: str
    source: str
    work_type: str | None = None
    score: int
    reasons: list[str]
    missing_skills: list[str]
    recommended_actions: list[str]


class MatchResultRun(BaseModel):
    run_id: UUID
    created_at: datetime
    normalized_profile: UserProfile
    generated_queries: list[QuerySpec]
    opportunities_top20: list[OpportunityClean]
    ranked_top5: list[OpportunityScore]
    coach_plan: dict[str, list[str]]
