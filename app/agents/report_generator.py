"""Report Generator Agent - Creates comprehensive final assessment."""
from __future__ import annotations

import json
from typing import Any, Dict, List
from uuid import UUID

from app.agents.base_agent import BaseInterviewAgent
from app.agents.prompts import REPORT_GENERATOR_PROMPT
from app.models.interview_schemas import (
    AnswerEvaluation,
    FinalReport,
    InterviewConfig,
    InterviewMemory,
    QuestionAnswer,
)


class ReportGeneratorAgent(BaseInterviewAgent):
    """Agent responsible for generating final interview reports."""
    
    def __init__(self, **kwargs):
        super().__init__(temperature=0.5, **kwargs)
    
    def get_prompt_template(self) -> str:
        return REPORT_GENERATOR_PROMPT
    
    def get_default_response(self) -> Dict[str, Any]:
        """Return default report if parsing fails."""
        return {
            "technical_level_estimate": "Mid",
            "communication_profile": "Average communicator with room for improvement.",
            "behavioral_maturity": "Demonstrates standard professional behavior.",
            "hiring_risks": [],
            "improvement_plan": "Focus on structured communication and technical depth.",
            "overall_score": 3.0,
            "strengths": ["Participated in interview", "Attempted all questions"],
            "weaknesses": ["Could not fully assess performance"],
            "recommendations": "Further Discussion - Additional interview recommended for comprehensive assessment."
        }
    
    def _format_all_evaluations(
        self,
        answers: List[QuestionAnswer],
    ) -> str:
        """Format all answers and evaluations for the prompt."""
        if not answers:
            return "No answers recorded."
        
        formatted = []
        for i, qa in enumerate(answers, 1):
            entry = f"--- Question {i} ({qa.state}) ---\n"
            entry += f"Q: {qa.question}\n"
            entry += f"A: {qa.answer}\n"
            if qa.evaluation:
                entry += f"Scores: Technical={qa.evaluation.technical_score}, "
                entry += f"Reasoning={qa.evaluation.reasoning_depth}, "
                entry += f"Communication={qa.evaluation.communication_clarity}, "
                entry += f"Structure={qa.evaluation.structure_score}, "
                entry += f"Confidence={qa.evaluation.confidence_signals}\n"
                entry += f"Average: {qa.evaluation.average_score:.2f}\n"
                if qa.evaluation.issues_detected:
                    entry += f"Issues: {', '.join(qa.evaluation.issues_detected)}\n"
                entry += f"Feedback: {qa.evaluation.feedback}"
            formatted.append(entry)
        
        return "\n\n".join(formatted)
    
    def _format_memory_analysis(self, memory: InterviewMemory) -> str:
        """Format memory analysis for the prompt."""
        return json.dumps({
            "weak_areas": memory.weak_areas,
            "strong_areas": memory.strong_areas,
            "performance_trend": memory.performance_trend,
            "average_score": memory.average_score,
            "communication_patterns": {
                "rambling_count": memory.communication_patterns.rambling,
                "unclear_count": memory.communication_patterns.unclear,
                "structured_count": memory.communication_patterns.structured,
                "confident_count": memory.communication_patterns.confident,
                "hesitant_count": memory.communication_patterns.hesitant,
            },
            "total_questions": len(memory.asked_questions),
        }, indent=2)
    
    async def generate(
        self,
        session_id: UUID,
        config: InterviewConfig,
        answers: List[QuestionAnswer],
        memory: InterviewMemory,
    ) -> FinalReport:
        """Generate comprehensive final report."""
        # Calculate communication profile summary
        comm_profile = self._generate_communication_summary(memory)
        
        response = await self.invoke(
            role=config.target_role,
            experience_level=config.experience_level.value if hasattr(config.experience_level, 'value') else config.experience_level,
            questions_count=len(answers),
            average_score=f"{memory.average_score:.2f}",
            communication_profile=comm_profile,
            all_evaluations=self._format_all_evaluations(answers),
            memory_analysis=self._format_memory_analysis(memory),
        )
        
        parsed = self.parse_json_response(response)
        
        return FinalReport(
            session_id=session_id,
            technical_level_estimate=parsed.get("technical_level_estimate", "Mid"),
            communication_profile=parsed.get("communication_profile", ""),
            behavioral_maturity=parsed.get("behavioral_maturity", ""),
            hiring_risks=parsed.get("hiring_risks", []),
            improvement_plan=parsed.get("improvement_plan", ""),
            overall_score=self._clamp_score(parsed.get("overall_score", 3.0)),
            strengths=parsed.get("strengths", []),
            weaknesses=parsed.get("weaknesses", []),
            recommendations=parsed.get("recommendations", ""),
            detailed_breakdown={
                "answers_count": len(answers),
                "memory": self._format_memory_analysis(memory),
            },
        )
    
    def generate_sync(
        self,
        session_id: UUID,
        config: InterviewConfig,
        answers: List[QuestionAnswer],
        memory: InterviewMemory,
    ) -> FinalReport:
        """Synchronous version of generate."""
        # Calculate communication profile summary
        comm_profile = self._generate_communication_summary(memory)
        
        response = self.invoke_sync(
            role=config.target_role,
            experience_level=config.experience_level.value if hasattr(config.experience_level, 'value') else config.experience_level,
            questions_count=len(answers),
            average_score=f"{memory.average_score:.2f}",
            communication_profile=comm_profile,
            all_evaluations=self._format_all_evaluations(answers),
            memory_analysis=self._format_memory_analysis(memory),
        )
        
        parsed = self.parse_json_response(response)
        
        return FinalReport(
            session_id=session_id,
            technical_level_estimate=parsed.get("technical_level_estimate", "Mid"),
            communication_profile=parsed.get("communication_profile", ""),
            behavioral_maturity=parsed.get("behavioral_maturity", ""),
            hiring_risks=parsed.get("hiring_risks", []),
            improvement_plan=parsed.get("improvement_plan", ""),
            overall_score=self._clamp_score(parsed.get("overall_score", 3.0)),
            strengths=parsed.get("strengths", []),
            weaknesses=parsed.get("weaknesses", []),
            recommendations=parsed.get("recommendations", ""),
            detailed_breakdown={
                "answers_count": len(answers),
                "memory": self._format_memory_analysis(memory),
            },
        )
    
    def _generate_communication_summary(self, memory: InterviewMemory) -> str:
        """Generate a brief communication profile summary."""
        patterns = memory.communication_patterns
        
        traits = []
        if patterns.structured > patterns.rambling:
            traits.append("structured")
        elif patterns.rambling > patterns.structured:
            traits.append("tends to ramble")
        
        if patterns.confident > patterns.hesitant:
            traits.append("confident")
        elif patterns.hesitant > patterns.confident:
            traits.append("somewhat hesitant")
        
        if patterns.unclear > 0:
            traits.append("occasionally unclear")
        
        if not traits:
            traits.append("neutral communication style")
        
        return ", ".join(traits)
    
    @staticmethod
    def _clamp_score(score: float) -> float:
        """Ensure score is within valid range."""
        try:
            score = float(score)
            return max(0.0, min(5.0, round(score, 2)))
        except (ValueError, TypeError):
            return 3.0
