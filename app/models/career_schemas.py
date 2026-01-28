"""Career Translator data models."""
from __future__ import annotations

from typing import List, Optional
from pydantic import BaseModel, Field


# Input Models
class LectureInput(BaseModel):
    """Input from other agents or API."""
    lecture_topic: str = Field(description="The topic of the lecture")
    lecture_text: Optional[str] = Field(default=None, description="Optional detailed lecture content")


# Output Sub-Models
class RealWorldRelevance(BaseModel):
    """Real-world relevance of the lecture topic."""
    where_used: List[str] = Field(description="System/context examples where this is used")
    problems_it_solves: List[str] = Field(description="Real problems this concept solves")
    risk_if_not_known: str = Field(description="Production failure or business impact if not understood")


class IndustryUseCase(BaseModel):
    """Industry use case for the concept."""
    domain: str = Field(description="AI / Backend / Cloud / Security / etc")
    scenario: str = Field(description="Real situation where this is applied")
    how_concept_is_used: str = Field(description="Practical application details")


class CompanyStyleTask(BaseModel):
    """Company-style practical task."""
    task_title: str = Field(description="Short realistic title")
    company_context: str = Field(description="Startup / Big tech / Product team situation")
    your_mission: str = Field(description="What the learner must do")
    constraints: List[str] = Field(description="Time, performance, data, cost limits")
    expected_output: str = Field(description="Deliverable expected")


class SkillsBuilt(BaseModel):
    """Skills developed from learning this concept."""
    technical: List[str] = Field(description="Hard skills developed")
    engineering_thinking: List[str] = Field(description="System design thinking, performance awareness")
    problem_solving: List[str] = Field(description="Debugging, optimization skills")
    team_relevance: List[str] = Field(description="Collaboration impact")


class CareerImpact(BaseModel):
    """Career impact of mastering this concept."""
    relevant_roles: List[str] = Field(description="ML Engineer, Backend Dev, etc")
    interview_relevance: str = Field(description="How it appears in interviews")
    junior_vs_senior_difference: str = Field(description="How seniors apply this differently")


class AdvancedChallenge(BaseModel):
    """Industry-level advanced challenge."""
    title: str = Field(description="Challenge title")
    description: str = Field(description="Hard real-world extension problem")


# Main Output Model
class CareerTranslation(BaseModel):
    """Complete career translation output - strict JSON for FastAPI response."""
    lecture_topic: str
    real_world_relevance: RealWorldRelevance
    industry_use_cases: List[IndustryUseCase]
    company_style_tasks: List[CompanyStyleTask]
    skills_built: SkillsBuilt
    career_impact: CareerImpact
    advanced_challenge: AdvancedChallenge


# API Request/Response Models
class TranslateLectureRequest(BaseModel):
    """API request to translate a lecture."""
    lecture_topic: str = Field(description="The topic of the lecture")
    lecture_text: Optional[str] = Field(default=None, description="Optional detailed lecture content")


class TranslateLectureResponse(BaseModel):
    """API response with career translation."""
    success: bool = True
    data: CareerTranslation
