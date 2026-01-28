"""Difficulty Engine Agent - Adjusts question difficulty based on performance."""
from __future__ import annotations

from typing import Any, Dict, List

from app.agents.base_agent import BaseInterviewAgent
from app.agents.prompts import DIFFICULTY_ENGINE_PROMPT
from app.models.interview_schemas import (
    AnswerEvaluation,
    DifficultyAdjustment,
    InterviewState,
)


class DifficultyEngineAgent(BaseInterviewAgent):
    """Agent responsible for adjusting interview difficulty."""
    
    def __init__(self, **kwargs):
        super().__init__(temperature=0.2, **kwargs)  # Low temperature for consistent logic
    
    def get_prompt_template(self) -> str:
        return DIFFICULTY_ENGINE_PROMPT
    
    def get_default_response(self) -> Dict[str, Any]:
        """Return default adjustment if parsing fails."""
        return {
            "new_difficulty": 3,
            "reason": "Maintaining current difficulty level.",
            "recommendations": ["Continue with standard questions"],
            "next_question_focus": "General"
        }
    
    def _analyze_performance_patterns(
        self,
        evaluations: List[AnswerEvaluation],
    ) -> Dict[str, bool]:
        """Analyze performance patterns from evaluations."""
        if not evaluations:
            return {
                "high_tech_low_comm": False,
                "consistent_high": False,
                "declining": False,
                "comm_issues": False,
            }
        
        # Calculate averages
        avg_technical = sum(e.technical_score for e in evaluations) / len(evaluations)
        avg_communication = sum(e.communication_clarity for e in evaluations) / len(evaluations)
        
        # Check patterns
        high_tech_low_comm = avg_technical >= 4 and avg_communication < 3
        consistent_high = all(e.average_score >= 4 for e in evaluations)
        
        # Check declining trend (last 2 lower than first 2)
        declining = False
        if len(evaluations) >= 4:
            first_avg = sum(e.average_score for e in evaluations[:2]) / 2
            last_avg = sum(e.average_score for e in evaluations[-2:]) / 2
            declining = last_avg < first_avg - 0.5
        
        # Check for communication issues
        comm_issues = any(
            issue in ["rambling", "unclear", "verbose", "lack_of_structure"]
            for e in evaluations
            for issue in e.issues_detected
        )
        
        return {
            "high_tech_low_comm": high_tech_low_comm,
            "consistent_high": consistent_high,
            "declining": declining,
            "comm_issues": comm_issues,
        }
    
    async def adjust(
        self,
        evaluations: List[AnswerEvaluation],
        current_difficulty: int,
        current_state: InterviewState,
    ) -> DifficultyAdjustment:
        """Determine difficulty adjustment based on performance."""
        if not evaluations:
            return DifficultyAdjustment(
                new_difficulty=current_difficulty,
                reason="No evaluations yet to base adjustment on.",
                recommendations=["Continue with initial difficulty"],
                next_question_focus="General introduction",
            )
        
        # Calculate averages
        avg_technical = sum(e.technical_score for e in evaluations) / len(evaluations)
        avg_communication = sum(e.communication_clarity for e in evaluations) / len(evaluations)
        
        # Analyze patterns
        patterns = self._analyze_performance_patterns(evaluations)
        
        response = await self.invoke(
            avg_technical=f"{avg_technical:.2f}",
            avg_communication=f"{avg_communication:.2f}",
            questions_count=len(evaluations),
            current_difficulty=current_difficulty,
            high_tech_low_comm=patterns["high_tech_low_comm"],
            consistent_high=patterns["consistent_high"],
            declining=patterns["declining"],
            comm_issues=patterns["comm_issues"],
            current_state=current_state.value if hasattr(current_state, 'value') else current_state,
        )
        
        parsed = self.parse_json_response(response)
        
        return DifficultyAdjustment(
            new_difficulty=self._clamp_difficulty(parsed.get("new_difficulty", current_difficulty)),
            reason=parsed.get("reason", ""),
            recommendations=parsed.get("recommendations", []),
            next_question_focus=parsed.get("next_question_focus", ""),
        )
    
    def adjust_sync(
        self,
        evaluations: List[AnswerEvaluation],
        current_difficulty: int,
        current_state: InterviewState,
    ) -> DifficultyAdjustment:
        """Synchronous version of adjust."""
        if not evaluations:
            return DifficultyAdjustment(
                new_difficulty=current_difficulty,
                reason="No evaluations yet to base adjustment on.",
                recommendations=["Continue with initial difficulty"],
                next_question_focus="General introduction",
            )
        
        # Calculate averages
        avg_technical = sum(e.technical_score for e in evaluations) / len(evaluations)
        avg_communication = sum(e.communication_clarity for e in evaluations) / len(evaluations)
        
        # Analyze patterns
        patterns = self._analyze_performance_patterns(evaluations)
        
        response = self.invoke_sync(
            avg_technical=f"{avg_technical:.2f}",
            avg_communication=f"{avg_communication:.2f}",
            questions_count=len(evaluations),
            current_difficulty=current_difficulty,
            high_tech_low_comm=patterns["high_tech_low_comm"],
            consistent_high=patterns["consistent_high"],
            declining=patterns["declining"],
            comm_issues=patterns["comm_issues"],
            current_state=current_state.value if hasattr(current_state, 'value') else current_state,
        )
        
        parsed = self.parse_json_response(response)
        
        return DifficultyAdjustment(
            new_difficulty=self._clamp_difficulty(parsed.get("new_difficulty", current_difficulty)),
            reason=parsed.get("reason", ""),
            recommendations=parsed.get("recommendations", []),
            next_question_focus=parsed.get("next_question_focus", ""),
        )
    
    @staticmethod
    def _clamp_difficulty(difficulty: int) -> int:
        """Ensure difficulty is within valid range."""
        try:
            difficulty = int(difficulty)
            return max(1, min(5, difficulty))
        except (ValueError, TypeError):
            return 3
