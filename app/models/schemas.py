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


class CompanyProfile(BaseModel):
    """Company information for task simulation."""
    name: str
    type: str
    size: str
    focus_areas: str
    tech_stack: str
    key_challenges: str


class TaskContext(BaseModel):
    """Business context for the task."""
    company_overview: str
    target_users: str
    business_problem: str
    why_it_matters: str


class TaskOrigin(BaseModel):
    """How the task arrived."""
    requested_by: str
    trigger_event: str
    requirement_quality: str
    constraints: str
    egypt_consideration: str


class RoleInfo(BaseModel):
    """Role information in the company."""
    job_title: str
    responsibilities: str
    out_of_scope: str
    collaborators: str


class TechnicalDetails(BaseModel):
    """Technical task details."""
    task_description: str
    data_inputs: str
    expected_outputs: list[str]
    edge_cases: list[str]
    performance_requirements: list[str]
    integrations: str
    security_requirements: list[str]
    deployment_expectations: list[str]


class NonTechnicalRealities(BaseModel):
    """Real-world non-technical challenges."""
    ambiguities: list[str]
    tradeoffs: list[str]
    decisions_with_incomplete_info: list[str]
    communication_challenges: list[str]
    business_pressure: list[str]


class MindsetComparison(BaseModel):
    """Student vs professional mindset."""
    student_approach: list[str]
    professional_approach: list[str]


class SkillsTraining(BaseModel):
    """Skills this task trains."""
    technical_skills: list[str]
    system_design: list[str]
    decision_making: list[str]
    communication: list[str]
    handling_ambiguity: list[str]
    egypt_market: list[str]


class FinalChallenge(BaseModel):
    """Challenge details for the intern."""
    timeline: str
    deliverables: list[str]
    key_questions: list[str]
    success_criteria: list[str]


class TaskSimulationStructured(BaseModel):
    """Structured task simulation response."""
    company: CompanyProfile
    context: TaskContext
    origin: TaskOrigin
    role: RoleInfo
    technical: TechnicalDetails
    realities: NonTechnicalRealities
    mindset: MindsetComparison
    skills: SkillsTraining
    challenge: FinalChallenge
    mvp_focus: list[str]
    not_focus: list[str]
    goal: str


class TaskSimulationOutput(BaseModel):
    company_name: str
    task_title: str
    simulation: TaskSimulationStructured


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


class MatchResultRun(BaseModel):
    run_id: UUID
    created_at: datetime
    normalized_profile: UserProfile
    generated_queries: list[QuerySpec]
    opportunities_top20: list[OpportunityClean]
    ranked_top5: list[OpportunityScore]
