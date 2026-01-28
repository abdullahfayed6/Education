"""Interview system data models."""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class InterviewState(str, Enum):
    """Interview state machine states."""
    INTRO = "INTRO"
    WARMUP = "WARMUP"
    CORE_QUESTIONS = "CORE_QUESTIONS"
    PRESSURE_ROUND = "PRESSURE_ROUND"
    COMMUNICATION_TEST = "COMMUNICATION_TEST"
    CLOSING = "CLOSING"
    FEEDBACK = "FEEDBACK"


class ExperienceLevel(str, Enum):
    """Candidate experience levels."""
    JUNIOR = "Junior"
    MID = "Mid"
    SENIOR = "Senior"
    EXPERT = "Expert"


class CompanyType(str, Enum):
    """Company types for interview context."""
    FAANG = "FAANG"
    STARTUP = "Startup"
    ENTERPRISE = "Enterprise"
    CONSULTING = "Consulting"
    AGENCY = "Agency"


class InterviewType(str, Enum):
    """Types of interviews."""
    TECHNICAL = "Technical"
    BEHAVIORAL = "Behavioral"
    COMMUNICATION = "Communication"
    MIXED = "Mixed"


class LeadershipLevel(str, Enum):
    """Leadership levels."""
    NONE = "None"
    TEAM_LEAD = "Team Lead"
    MANAGER = "Manager"
    DIRECTOR = "Director"


class Scale(str, Enum):
    """Interview scale/depth."""
    SMALL = "Small"
    MEDIUM = "Medium"
    LARGE = "Large"


class InterviewConfig(BaseModel):
    """Configuration for an interview session."""
    target_role: str = Field(description="e.g., 'Backend Engineer', 'Data Scientist'")
    experience_level: ExperienceLevel = ExperienceLevel.MID
    company_type: CompanyType = CompanyType.STARTUP
    interview_type: InterviewType = InterviewType.MIXED
    difficulty: int = Field(default=3, ge=1, le=5)
    tech_stack: list[str] = Field(default_factory=list, description="e.g., ['Python', 'SQL', 'AWS']")
    focus_area: str = Field(default="General", description="e.g., 'System Design', 'Algorithms'")
    allow_coding: bool = False
    scale: Scale = Scale.MEDIUM
    leadership_level: LeadershipLevel = LeadershipLevel.NONE
    focus_traits: list[str] = Field(default_factory=lambda: ["Problem Solving", "Communication"])
    communication_strictness: int = Field(default=3, ge=1, le=5)
    allow_interruptions: bool = False
    time_pressure: bool = False


class AnswerEvaluation(BaseModel):
    """Evaluation of a candidate's answer."""
    technical_score: int = Field(ge=1, le=5, description="Correctness and depth of technical knowledge")
    reasoning_depth: int = Field(ge=1, le=5, description="Quality of explanation and thought process")
    communication_clarity: int = Field(ge=1, le=5, description="How well the answer was explained")
    structure_score: int = Field(ge=1, le=5, description="Organization and logical flow")
    confidence_signals: int = Field(ge=1, le=5, description="Signs of confidence and conviction")
    issues_detected: list[str] = Field(default_factory=list, description="e.g., ['rambling', 'lack_of_structure']")
    feedback: str = Field(default="", description="Constructive feedback for improvement")
    follow_up_suggestion: str = Field(default="", description="Suggested follow-up question")
    
    @property
    def average_score(self) -> float:
        """Calculate average score across all dimensions."""
        return (
            self.technical_score + 
            self.reasoning_depth + 
            self.communication_clarity + 
            self.structure_score + 
            self.confidence_signals
        ) / 5.0


class QuestionAnswer(BaseModel):
    """A question-answer pair with evaluation."""
    question: str
    answer: str
    state: InterviewState
    difficulty: int
    evaluation: Optional[AnswerEvaluation] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class CommunicationPatterns(BaseModel):
    """Tracked communication patterns."""
    rambling: int = 0
    unclear: int = 0
    structured: int = 0
    verbose: int = 0
    hesitant: int = 0
    confident: int = 0


class InterviewMemory(BaseModel):
    """Memory tracking for the interview session."""
    asked_questions: list[str] = Field(default_factory=list)
    weak_areas: list[str] = Field(default_factory=list)
    strong_areas: list[str] = Field(default_factory=list)
    communication_patterns: CommunicationPatterns = Field(default_factory=CommunicationPatterns)
    performance_trend: str = "stable"  # improving, declining, stable
    average_score: float = 0.0


class CommunicationAnalysis(BaseModel):
    """Communication coach analysis result."""
    overall_communication_score: int = Field(ge=1, le=5)
    patterns_detected: list[str] = Field(default_factory=list)
    specific_issues: str = ""
    recommendations: str = ""
    strengths: str = ""


class DifficultyAdjustment(BaseModel):
    """Difficulty engine adjustment result."""
    new_difficulty: int = Field(ge=1, le=5)
    reason: str = ""
    recommendations: list[str] = Field(default_factory=list)
    next_question_focus: str = ""


class StateTransition(BaseModel):
    """Session manager state transition result."""
    should_transition: bool = False
    next_state: InterviewState = InterviewState.INTRO
    reason: str = ""
    state_instructions: str = ""


class InterviewSession(BaseModel):
    """Complete interview session data."""
    session_id: UUID = Field(default_factory=uuid4)
    user_id: str
    config: InterviewConfig
    current_state: InterviewState = InterviewState.INTRO
    questions_asked: int = 0
    answers: list[QuestionAnswer] = Field(default_factory=list)
    evaluations: list[AnswerEvaluation] = Field(default_factory=list)
    memory: InterviewMemory = Field(default_factory=InterviewMemory)
    current_difficulty: int = 3
    overall_score: float = 0.0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    is_complete: bool = False
    
    class Config:
        """Pydantic config."""
        use_enum_values = True


class FinalReport(BaseModel):
    """Final interview assessment report."""
    session_id: UUID
    technical_level_estimate: str
    communication_profile: str
    behavioral_maturity: str
    hiring_risks: list[str] = Field(default_factory=list)
    improvement_plan: str = ""
    overall_score: float = Field(ge=0, le=5)
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    recommendations: str = ""
    detailed_breakdown: dict = Field(default_factory=dict)
    generated_at: datetime = Field(default_factory=datetime.utcnow)


# API Request/Response Models
class StartInterviewRequest(BaseModel):
    """Request to start a new interview."""
    user_id: str
    config: InterviewConfig


class StartInterviewResponse(BaseModel):
    """Response when starting an interview."""
    session_id: UUID
    first_question: str
    state: InterviewState
    difficulty: int


class SubmitAnswerRequest(BaseModel):
    """Request to submit an answer."""
    session_id: UUID
    question: str
    answer: str


class SubmitAnswerResponse(BaseModel):
    """Response after submitting an answer."""
    evaluation: AnswerEvaluation
    feedback: str
    difficulty_adjustment: DifficultyAdjustment
    next_state: InterviewState
    next_question: Optional[str] = None
    is_complete: bool = False


class SessionStatusResponse(BaseModel):
    """Response for session status query."""
    session_id: UUID
    current_state: InterviewState
    questions_asked: int
    average_score: float
    current_difficulty: int
    is_complete: bool
    performance_trend: str
