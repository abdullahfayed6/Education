"""Memory Agent - Tracks performance history and patterns."""
from __future__ import annotations

import json
from typing import Any, Dict, List

from app.agents.base_agent import BaseInterviewAgent
from app.agents.prompts import MEMORY_AGENT_PROMPT
from app.models.interview_schemas import (
    AnswerEvaluation,
    CommunicationPatterns,
    InterviewMemory,
)


class MemoryAgent(BaseInterviewAgent):
    """Agent responsible for tracking and updating interview memory."""
    
    def __init__(self, **kwargs):
        super().__init__(temperature=0.1, **kwargs)  # Very low temperature for consistent tracking
    
    def get_prompt_template(self) -> str:
        return MEMORY_AGENT_PROMPT
    
    def get_default_response(self) -> Dict[str, Any]:
        """Return default memory if parsing fails."""
        return {
            "asked_questions": [],
            "weak_areas": [],
            "strong_areas": [],
            "communication_patterns": {
                "rambling": 0,
                "unclear": 0,
                "structured": 0,
                "verbose": 0,
                "hesitant": 0,
                "confident": 0,
            },
            "performance_trend": "stable",
            "average_score": 0.0,
        }
    
    def _format_memory(self, memory: InterviewMemory) -> str:
        """Format current memory for the prompt."""
        return json.dumps({
            "asked_questions": memory.asked_questions,
            "weak_areas": memory.weak_areas,
            "strong_areas": memory.strong_areas,
            "communication_patterns": {
                "rambling": memory.communication_patterns.rambling,
                "unclear": memory.communication_patterns.unclear,
                "structured": memory.communication_patterns.structured,
                "verbose": memory.communication_patterns.verbose,
                "hesitant": memory.communication_patterns.hesitant,
                "confident": memory.communication_patterns.confident,
            },
            "performance_trend": memory.performance_trend,
            "average_score": memory.average_score,
        }, indent=2)
    
    def _format_evaluation(self, evaluation: AnswerEvaluation) -> str:
        """Format evaluation for the prompt."""
        return json.dumps({
            "technical_score": evaluation.technical_score,
            "reasoning_depth": evaluation.reasoning_depth,
            "communication_clarity": evaluation.communication_clarity,
            "structure_score": evaluation.structure_score,
            "confidence_signals": evaluation.confidence_signals,
            "average_score": evaluation.average_score,
            "issues_detected": evaluation.issues_detected,
        }, indent=2)
    
    async def update(
        self,
        current_memory: InterviewMemory,
        new_evaluation: AnswerEvaluation,
        question: str,
    ) -> InterviewMemory:
        """Update memory with new evaluation data."""
        response = await self.invoke(
            current_memory=self._format_memory(current_memory),
            new_evaluation=self._format_evaluation(new_evaluation),
            question=question,
        )
        
        parsed = self.parse_json_response(response)
        
        # Parse communication patterns
        comm_patterns_raw = parsed.get("communication_patterns", {})
        comm_patterns = CommunicationPatterns(
            rambling=comm_patterns_raw.get("rambling", 0),
            unclear=comm_patterns_raw.get("unclear", 0),
            structured=comm_patterns_raw.get("structured", 0),
            verbose=comm_patterns_raw.get("verbose", 0),
            hesitant=comm_patterns_raw.get("hesitant", 0),
            confident=comm_patterns_raw.get("confident", 0),
        )
        
        return InterviewMemory(
            asked_questions=parsed.get("asked_questions", current_memory.asked_questions + [question]),
            weak_areas=parsed.get("weak_areas", current_memory.weak_areas),
            strong_areas=parsed.get("strong_areas", current_memory.strong_areas),
            communication_patterns=comm_patterns,
            performance_trend=parsed.get("performance_trend", "stable"),
            average_score=float(parsed.get("average_score", 0.0)),
        )
    
    def update_sync(
        self,
        current_memory: InterviewMemory,
        new_evaluation: AnswerEvaluation,
        question: str,
    ) -> InterviewMemory:
        """Synchronous version of update."""
        response = self.invoke_sync(
            current_memory=self._format_memory(current_memory),
            new_evaluation=self._format_evaluation(new_evaluation),
            question=question,
        )
        
        parsed = self.parse_json_response(response)
        
        # Parse communication patterns
        comm_patterns_raw = parsed.get("communication_patterns", {})
        comm_patterns = CommunicationPatterns(
            rambling=comm_patterns_raw.get("rambling", 0),
            unclear=comm_patterns_raw.get("unclear", 0),
            structured=comm_patterns_raw.get("structured", 0),
            verbose=comm_patterns_raw.get("verbose", 0),
            hesitant=comm_patterns_raw.get("hesitant", 0),
            confident=comm_patterns_raw.get("confident", 0),
        )
        
        return InterviewMemory(
            asked_questions=parsed.get("asked_questions", current_memory.asked_questions + [question]),
            weak_areas=parsed.get("weak_areas", current_memory.weak_areas),
            strong_areas=parsed.get("strong_areas", current_memory.strong_areas),
            communication_patterns=comm_patterns,
            performance_trend=parsed.get("performance_trend", "stable"),
            average_score=float(parsed.get("average_score", 0.0)),
        )
    
    def update_simple(
        self,
        current_memory: InterviewMemory,
        new_evaluation: AnswerEvaluation,
        question: str,
        all_evaluations: List[AnswerEvaluation],
    ) -> InterviewMemory:
        """Simple memory update without LLM call for faster processing."""
        # Add question to history
        asked_questions = current_memory.asked_questions + [question]
        
        # Calculate new average
        avg_score = new_evaluation.average_score
        if all_evaluations:
            avg_score = sum(e.average_score for e in all_evaluations) / len(all_evaluations)
        
        # Update weak/strong areas based on score
        weak_areas = list(current_memory.weak_areas)
        strong_areas = list(current_memory.strong_areas)
        
        # Determine area from question (simplified)
        area = self._extract_area_from_question(question)
        
        if new_evaluation.average_score < 2.5 and area and area not in weak_areas:
            weak_areas.append(area)
        elif new_evaluation.average_score >= 4 and area and area not in strong_areas:
            strong_areas.append(area)
        
        # Update communication patterns
        patterns = CommunicationPatterns(
            rambling=current_memory.communication_patterns.rambling + (1 if "rambling" in new_evaluation.issues_detected else 0),
            unclear=current_memory.communication_patterns.unclear + (1 if "unclear" in new_evaluation.issues_detected else 0),
            structured=current_memory.communication_patterns.structured + (1 if new_evaluation.structure_score >= 4 else 0),
            verbose=current_memory.communication_patterns.verbose + (1 if "verbose" in new_evaluation.issues_detected else 0),
            hesitant=current_memory.communication_patterns.hesitant + (1 if new_evaluation.confidence_signals <= 2 else 0),
            confident=current_memory.communication_patterns.confident + (1 if new_evaluation.confidence_signals >= 4 else 0),
        )
        
        # Determine trend
        trend = "stable"
        if len(all_evaluations) >= 4:
            first_avg = sum(e.average_score for e in all_evaluations[:2]) / 2
            last_avg = sum(e.average_score for e in all_evaluations[-2:]) / 2
            if last_avg > first_avg + 0.3:
                trend = "improving"
            elif last_avg < first_avg - 0.3:
                trend = "declining"
        
        return InterviewMemory(
            asked_questions=asked_questions,
            weak_areas=weak_areas,
            strong_areas=strong_areas,
            communication_patterns=patterns,
            performance_trend=trend,
            average_score=round(avg_score, 2),
        )
    
    @staticmethod
    def _extract_area_from_question(question: str) -> str:
        """Extract the topic area from a question (simplified)."""
        question_lower = question.lower()
        
        # Common technical areas
        areas = [
            "algorithms", "data structures", "system design", "databases",
            "api", "microservices", "testing", "debugging", "performance",
            "security", "networking", "cloud", "devops", "leadership",
            "teamwork", "communication", "problem solving", "coding",
        ]
        
        for area in areas:
            if area in question_lower:
                return area.title()
        
        return ""
