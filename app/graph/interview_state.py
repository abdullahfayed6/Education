"""LangGraph state definition for the interview workflow."""
from __future__ import annotations

from typing import TypedDict, Optional, List, Dict, Any

from app.models.interview_schemas import (
    InterviewConfig,
    InterviewState,
    QuestionAnswer,
    AnswerEvaluation,
    InterviewMemory,
    CommunicationAnalysis,
    DifficultyAdjustment,
    StateTransition,
    FinalReport,
)


class InterviewGraphState(TypedDict, total=False):
    """State that flows through the LangGraph interview workflow."""
    
    # Session identifiers
    session_id: str
    user_id: str
    
    # Configuration
    config: InterviewConfig
    
    # Current state
    current_state: InterviewState
    current_difficulty: int
    questions_asked: int
    
    # Current question/answer being processed
    current_question: str
    current_answer: str
    
    # History
    answers: List[QuestionAnswer]
    evaluations: List[AnswerEvaluation]
    
    # Memory tracking
    memory: InterviewMemory
    
    # Agent outputs
    evaluation_result: AnswerEvaluation
    communication_analysis: CommunicationAnalysis
    difficulty_adjustment: DifficultyAdjustment
    state_transition: StateTransition
    next_question: str
    
    # Final output
    final_report: FinalReport
    overall_score: float
    is_complete: bool
    
    # Error handling
    error: Optional[str]


# State constants for interview flow
STATE_QUESTION_LIMITS = {
    InterviewState.INTRO: 1,
    InterviewState.WARMUP: 1,
    InterviewState.CORE_QUESTIONS: 3,
    InterviewState.PRESSURE_ROUND: 2,
    InterviewState.COMMUNICATION_TEST: 1,
    InterviewState.CLOSING: 1,
    InterviewState.FEEDBACK: 0,
}

STATE_ORDER = [
    InterviewState.INTRO,
    InterviewState.WARMUP,
    InterviewState.CORE_QUESTIONS,
    InterviewState.PRESSURE_ROUND,
    InterviewState.COMMUNICATION_TEST,
    InterviewState.CLOSING,
    InterviewState.FEEDBACK,
]


def get_next_state(current_state: InterviewState) -> InterviewState:
    """Get the next state in the interview flow."""
    current_index = STATE_ORDER.index(current_state)
    if current_index < len(STATE_ORDER) - 1:
        return STATE_ORDER[current_index + 1]
    return InterviewState.FEEDBACK


def get_questions_for_state(state: InterviewState) -> int:
    """Get the number of questions expected for a given state."""
    return STATE_QUESTION_LIMITS.get(state, 1)
