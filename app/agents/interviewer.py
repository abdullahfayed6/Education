"""Interviewer Agent - Generates contextual interview questions."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.agents.base_agent import BaseInterviewAgent
from app.agents.prompts import INTERVIEWER_PROMPT
from app.models.interview_schemas import InterviewConfig, InterviewState, InterviewMemory


class InterviewerAgent(BaseInterviewAgent):
    """Agent responsible for generating interview questions."""
    
    def __init__(self, **kwargs):
        super().__init__(temperature=0.8, **kwargs)
    
    def get_prompt_template(self) -> str:
        return INTERVIEWER_PROMPT
    
    async def generate_question(
        self,
        config: InterviewConfig,
        current_state: InterviewState,
        difficulty: int,
        questions_asked: int,
        memory: InterviewMemory,
    ) -> str:
        """Generate a question appropriate for the current interview state."""
        # Format previous questions
        previous_questions = "\n".join(
            f"- {q}" for q in memory.asked_questions
        ) if memory.asked_questions else "None yet"
        
        # Format weak and strong areas
        weak_areas = ", ".join(memory.weak_areas) if memory.weak_areas else "None identified yet"
        strong_areas = ", ".join(memory.strong_areas) if memory.strong_areas else "None identified yet"
        
        # Format tech stack
        tech_stack = ", ".join(config.tech_stack) if config.tech_stack else "General"
        
        response = await self.invoke(
            role=config.target_role,
            experience_level=config.experience_level.value if hasattr(config.experience_level, 'value') else config.experience_level,
            company_type=config.company_type.value if hasattr(config.company_type, 'value') else config.company_type,
            interview_type=config.interview_type.value if hasattr(config.interview_type, 'value') else config.interview_type,
            difficulty=difficulty,
            current_state=current_state.value if hasattr(current_state, 'value') else current_state,
            questions_asked=questions_asked,
            tech_stack=tech_stack,
            focus_area=config.focus_area,
            previous_questions=previous_questions,
            weak_areas=weak_areas,
            strong_areas=strong_areas,
        )
        
        # Clean up the response - remove any extra formatting
        question = response.strip()
        if question.startswith('"') and question.endswith('"'):
            question = question[1:-1]
        
        return question
    
    def generate_question_sync(
        self,
        config: InterviewConfig,
        current_state: InterviewState,
        difficulty: int,
        questions_asked: int,
        memory: InterviewMemory,
    ) -> str:
        """Synchronous version of generate_question."""
        # Format previous questions
        previous_questions = "\n".join(
            f"- {q}" for q in memory.asked_questions
        ) if memory.asked_questions else "None yet"
        
        # Format weak and strong areas
        weak_areas = ", ".join(memory.weak_areas) if memory.weak_areas else "None identified yet"
        strong_areas = ", ".join(memory.strong_areas) if memory.strong_areas else "None identified yet"
        
        # Format tech stack
        tech_stack = ", ".join(config.tech_stack) if config.tech_stack else "General"
        
        response = self.invoke_sync(
            role=config.target_role,
            experience_level=config.experience_level.value if hasattr(config.experience_level, 'value') else config.experience_level,
            company_type=config.company_type.value if hasattr(config.company_type, 'value') else config.company_type,
            interview_type=config.interview_type.value if hasattr(config.interview_type, 'value') else config.interview_type,
            difficulty=difficulty,
            current_state=current_state.value if hasattr(current_state, 'value') else current_state,
            questions_asked=questions_asked,
            tech_stack=tech_stack,
            focus_area=config.focus_area,
            previous_questions=previous_questions,
            weak_areas=weak_areas,
            strong_areas=strong_areas,
        )
        
        # Clean up the response
        question = response.strip()
        if question.startswith('"') and question.endswith('"'):
            question = question[1:-1]
        
        return question
