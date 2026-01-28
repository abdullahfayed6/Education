"""Answer Analyzer Agent - Evaluates candidate responses."""
from __future__ import annotations

from typing import Any, Dict

from app.agents.base_agent import BaseInterviewAgent
from app.agents.prompts import ANSWER_ANALYZER_PROMPT
from app.models.interview_schemas import (
    AnswerEvaluation,
    InterviewConfig,
    InterviewState,
)


class AnswerAnalyzerAgent(BaseInterviewAgent):
    """Agent responsible for evaluating candidate answers."""
    
    def __init__(self, **kwargs):
        super().__init__(temperature=0.3, **kwargs)  # Lower temperature for consistent evaluation
    
    def get_prompt_template(self) -> str:
        return ANSWER_ANALYZER_PROMPT
    
    def get_default_response(self) -> Dict[str, Any]:
        """Return default evaluation if parsing fails."""
        return {
            "technical_score": 3,
            "reasoning_depth": 3,
            "communication_clarity": 3,
            "structure_score": 3,
            "confidence_signals": 3,
            "issues_detected": [],
            "feedback": "Unable to fully evaluate the response.",
            "follow_up": "Could you elaborate on your answer?"
        }
    
    async def evaluate(
        self,
        question: str,
        answer: str,
        config: InterviewConfig,
        difficulty: int,
        current_state: InterviewState,
    ) -> AnswerEvaluation:
        """Evaluate a candidate's answer."""
        response = await self.invoke(
            question=question,
            answer=answer,
            role=config.target_role,
            experience_level=config.experience_level.value if hasattr(config.experience_level, 'value') else config.experience_level,
            difficulty=difficulty,
            current_state=current_state.value if hasattr(current_state, 'value') else current_state,
        )
        
        parsed = self.parse_json_response(response)
        
        return AnswerEvaluation(
            technical_score=self._clamp_score(parsed.get("technical_score", 3)),
            reasoning_depth=self._clamp_score(parsed.get("reasoning_depth", 3)),
            communication_clarity=self._clamp_score(parsed.get("communication_clarity", 3)),
            structure_score=self._clamp_score(parsed.get("structure_score", 3)),
            confidence_signals=self._clamp_score(parsed.get("confidence_signals", 3)),
            issues_detected=parsed.get("issues_detected", []),
            feedback=parsed.get("feedback", ""),
            follow_up_suggestion=parsed.get("follow_up", ""),
        )
    
    def evaluate_sync(
        self,
        question: str,
        answer: str,
        config: InterviewConfig,
        difficulty: int,
        current_state: InterviewState,
    ) -> AnswerEvaluation:
        """Synchronous version of evaluate."""
        response = self.invoke_sync(
            question=question,
            answer=answer,
            role=config.target_role,
            experience_level=config.experience_level.value if hasattr(config.experience_level, 'value') else config.experience_level,
            difficulty=difficulty,
            current_state=current_state.value if hasattr(current_state, 'value') else current_state,
        )
        
        parsed = self.parse_json_response(response)
        
        return AnswerEvaluation(
            technical_score=self._clamp_score(parsed.get("technical_score", 3)),
            reasoning_depth=self._clamp_score(parsed.get("reasoning_depth", 3)),
            communication_clarity=self._clamp_score(parsed.get("communication_clarity", 3)),
            structure_score=self._clamp_score(parsed.get("structure_score", 3)),
            confidence_signals=self._clamp_score(parsed.get("confidence_signals", 3)),
            issues_detected=parsed.get("issues_detected", []),
            feedback=parsed.get("feedback", ""),
            follow_up_suggestion=parsed.get("follow_up", ""),
        )
    
    @staticmethod
    def _clamp_score(score: int) -> int:
        """Ensure score is within valid range."""
        try:
            score = int(score)
            return max(1, min(5, score))
        except (ValueError, TypeError):
            return 3
