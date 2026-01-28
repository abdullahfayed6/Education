"""Session Manager Agent - Orchestrates interview flow and state transitions."""
from __future__ import annotations

from typing import Any, Dict

from app.agents.base_agent import BaseInterviewAgent
from app.agents.prompts import SESSION_MANAGER_PROMPT
from app.models.interview_schemas import InterviewState, StateTransition
from app.graph.interview_state import STATE_QUESTION_LIMITS, get_next_state


class SessionManagerAgent(BaseInterviewAgent):
    """Agent responsible for managing interview state transitions."""
    
    def __init__(self, **kwargs):
        super().__init__(temperature=0.2, **kwargs)  # Low temperature for consistent logic
    
    def get_prompt_template(self) -> str:
        return SESSION_MANAGER_PROMPT
    
    def get_default_response(self) -> Dict[str, Any]:
        """Return default transition if parsing fails."""
        return {
            "should_transition": False,
            "next_state": "CORE_QUESTIONS",
            "reason": "Unable to determine transition, continuing current state.",
            "state_instructions": "Continue with current interview flow."
        }
    
    async def check_transition(
        self,
        current_state: InterviewState,
        questions_in_state: int,
        total_questions: int,
        average_score: float,
        performance_trend: str,
    ) -> StateTransition:
        """Check if state transition is needed."""
        response = await self.invoke(
            current_state=current_state.value if hasattr(current_state, 'value') else current_state,
            questions_in_state=questions_in_state,
            total_questions=total_questions,
            average_score=f"{average_score:.2f}",
            performance_trend=performance_trend,
        )
        
        parsed = self.parse_json_response(response)
        
        # Parse next state
        next_state_str = parsed.get("next_state", current_state.value if hasattr(current_state, 'value') else current_state)
        try:
            next_state = InterviewState(next_state_str)
        except ValueError:
            next_state = get_next_state(current_state)
        
        return StateTransition(
            should_transition=parsed.get("should_transition", False),
            next_state=next_state,
            reason=parsed.get("reason", ""),
            state_instructions=parsed.get("state_instructions", ""),
        )
    
    def check_transition_sync(
        self,
        current_state: InterviewState,
        questions_in_state: int,
        total_questions: int,
        average_score: float,
        performance_trend: str,
    ) -> StateTransition:
        """Synchronous version of check_transition."""
        response = self.invoke_sync(
            current_state=current_state.value if hasattr(current_state, 'value') else current_state,
            questions_in_state=questions_in_state,
            total_questions=total_questions,
            average_score=f"{average_score:.2f}",
            performance_trend=performance_trend,
        )
        
        parsed = self.parse_json_response(response)
        
        # Parse next state
        next_state_str = parsed.get("next_state", current_state.value if hasattr(current_state, 'value') else current_state)
        try:
            next_state = InterviewState(next_state_str)
        except ValueError:
            next_state = get_next_state(current_state)
        
        return StateTransition(
            should_transition=parsed.get("should_transition", False),
            next_state=next_state,
            reason=parsed.get("reason", ""),
            state_instructions=parsed.get("state_instructions", ""),
        )
    
    def check_transition_simple(
        self,
        current_state: InterviewState,
        questions_in_state: int,
    ) -> StateTransition:
        """Simple state transition check without LLM call."""
        # Get required questions for current state
        required = STATE_QUESTION_LIMITS.get(current_state, 1)
        
        # Check if we should transition
        should_transition = questions_in_state >= required
        
        if should_transition:
            next_state = get_next_state(current_state)
            
            # Generate state instructions
            state_instructions = self._get_state_instructions(next_state)
            
            return StateTransition(
                should_transition=True,
                next_state=next_state,
                reason=f"Completed {questions_in_state} question(s) in {current_state.value} state.",
                state_instructions=state_instructions,
            )
        else:
            return StateTransition(
                should_transition=False,
                next_state=current_state,
                reason=f"Need {required - questions_in_state} more question(s) in {current_state.value} state.",
                state_instructions=self._get_state_instructions(current_state),
            )
    
    @staticmethod
    def _get_state_instructions(state: InterviewState) -> str:
        """Get instructions for a given state."""
        instructions = {
            InterviewState.INTRO: "Start with a warm introduction. Ask the candidate to introduce themselves.",
            InterviewState.WARMUP: "Ask easy, foundational questions to build confidence.",
            InterviewState.CORE_QUESTIONS: "Ask main technical or behavioral questions based on the role and config.",
            InterviewState.PRESSURE_ROUND: "Ask challenging scenario-based questions with constraints and trade-offs.",
            InterviewState.COMMUNICATION_TEST: "Ask explanation-focused questions requiring clear articulation.",
            InterviewState.CLOSING: "Give the candidate a chance to ask questions. Summarize the interview.",
            InterviewState.FEEDBACK: "Generate the final report and conclude the interview.",
        }
        return instructions.get(state, "Continue with the interview flow.")
