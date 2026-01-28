"""Communication Coach Agent - Detects communication patterns and issues."""
from __future__ import annotations

from typing import Any, Dict, List

from app.agents.base_agent import BaseInterviewAgent
from app.agents.prompts import COMMUNICATION_COACH_PROMPT
from app.models.interview_schemas import (
    AnswerEvaluation,
    CommunicationAnalysis,
    QuestionAnswer,
)


class CommunicationCoachAgent(BaseInterviewAgent):
    """Agent responsible for analyzing communication patterns."""
    
    def __init__(self, **kwargs):
        super().__init__(temperature=0.4, **kwargs)
    
    def get_prompt_template(self) -> str:
        return COMMUNICATION_COACH_PROMPT
    
    def get_default_response(self) -> Dict[str, Any]:
        """Return default analysis if parsing fails."""
        return {
            "overall_communication_score": 3,
            "patterns_detected": [],
            "specific_issues": "",
            "recommendations": "Continue practicing clear and structured communication.",
            "strengths": "Attempting to communicate technical concepts."
        }
    
    def _format_answers_with_evaluations(
        self,
        answers: List[QuestionAnswer],
    ) -> str:
        """Format answers with their evaluations for the prompt."""
        if not answers:
            return "No answers to analyze yet."
        
        formatted = []
        for i, qa in enumerate(answers, 1):
            entry = f"Q{i}: {qa.question}\nA{i}: {qa.answer}"
            if qa.evaluation:
                entry += f"\nEvaluation: Communication={qa.evaluation.communication_clarity}/5, Structure={qa.evaluation.structure_score}/5"
                if qa.evaluation.issues_detected:
                    entry += f", Issues: {', '.join(qa.evaluation.issues_detected)}"
            formatted.append(entry)
        
        return "\n\n".join(formatted)
    
    async def analyze(
        self,
        answers: List[QuestionAnswer],
        communication_strictness: int,
    ) -> CommunicationAnalysis:
        """Analyze communication patterns across all answers."""
        formatted_answers = self._format_answers_with_evaluations(answers)
        
        response = await self.invoke(
            previous_answers_with_evaluations=formatted_answers,
            communication_strictness=communication_strictness,
        )
        
        parsed = self.parse_json_response(response)
        
        return CommunicationAnalysis(
            overall_communication_score=self._clamp_score(parsed.get("overall_communication_score", 3)),
            patterns_detected=parsed.get("patterns_detected", []),
            specific_issues=parsed.get("specific_issues", ""),
            recommendations=parsed.get("recommendations", ""),
            strengths=parsed.get("strengths", ""),
        )
    
    def analyze_sync(
        self,
        answers: List[QuestionAnswer],
        communication_strictness: int,
    ) -> CommunicationAnalysis:
        """Synchronous version of analyze."""
        formatted_answers = self._format_answers_with_evaluations(answers)
        
        response = self.invoke_sync(
            previous_answers_with_evaluations=formatted_answers,
            communication_strictness=communication_strictness,
        )
        
        parsed = self.parse_json_response(response)
        
        return CommunicationAnalysis(
            overall_communication_score=self._clamp_score(parsed.get("overall_communication_score", 3)),
            patterns_detected=parsed.get("patterns_detected", []),
            specific_issues=parsed.get("specific_issues", ""),
            recommendations=parsed.get("recommendations", ""),
            strengths=parsed.get("strengths", ""),
        )
    
    @staticmethod
    def _clamp_score(score: int) -> int:
        """Ensure score is within valid range."""
        try:
            score = int(score)
            return max(1, min(5, score))
        except (ValueError, TypeError):
            return 3
