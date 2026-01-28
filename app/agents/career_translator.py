"""Career Translator Agent - Converts academic lectures into industry value."""
from __future__ import annotations

import json
import logging
import re
from typing import Any, Dict

from app.agents.base_agent import BaseInterviewAgent
from app.agents.career_prompts import CAREER_TRANSLATOR_PROMPT
from app.models.career_schemas import (
    AdvancedChallenge,
    CareerImpact,
    CareerTranslation,
    CompanyStyleTask,
    IndustryUseCase,
    LectureInput,
    RealWorldRelevance,
    SkillsBuilt,
)

logger = logging.getLogger(__name__)


class CareerTranslatorAgent(BaseInterviewAgent):
    """
    Industry Mentor AI that translates academic lectures into career value.
    
    Converts lecture topics into:
    - Real-world relevance
    - Industry use cases
    - Company-style practical tasks
    - Skills developed
    - Career impact
    - Advanced challenges
    """
    
    def __init__(self, **kwargs):
        # Higher temperature for more creative industry examples
        super().__init__(model="gpt-4o-mini", temperature=0.7, **kwargs)
    
    def get_prompt_template(self) -> str:
        return CAREER_TRANSLATOR_PROMPT
    
    def get_default_response(self) -> Dict[str, Any]:
        """Return default translation if parsing fails."""
        return {
            "lecture_topic": "Unknown Topic",
            "real_world_relevance": {
                "where_used": ["Various production systems"],
                "problems_it_solves": ["Common engineering challenges"],
                "risk_if_not_known": "Potential system failures or inefficiencies"
            },
            "industry_use_cases": [
                {
                    "domain": "Software Engineering",
                    "scenario": "Building production systems",
                    "how_concept_is_used": "Applied in daily engineering work"
                }
            ],
            "company_style_tasks": [
                {
                    "task_title": "Apply Concept in Practice",
                    "company_context": "Standard engineering team",
                    "your_mission": "Implement the concept in a real scenario",
                    "constraints": ["Complete within 4 hours", "Follow best practices"],
                    "expected_output": "Working implementation with documentation"
                }
            ],
            "skills_built": {
                "technical": ["Core technical competency"],
                "engineering_thinking": ["Systems thinking"],
                "problem_solving": ["Analytical skills"],
                "team_relevance": ["Technical communication"]
            },
            "career_impact": {
                "relevant_roles": ["Software Engineer", "Backend Developer"],
                "interview_relevance": "Commonly asked in technical interviews",
                "junior_vs_senior_difference": "Seniors apply this with deeper system understanding"
            },
            "advanced_challenge": {
                "title": "Scale the Solution",
                "description": "Extend the implementation to handle enterprise-scale requirements"
            }
        }
    
    async def translate(self, lecture_input: LectureInput) -> CareerTranslation:
        """
        Translate a lecture into career-relevant content.
        
        Args:
            lecture_input: The lecture topic and optional content
            
        Returns:
            CareerTranslation with structured industry insights
        """
        lecture_text = lecture_input.lecture_text or "No additional content provided. Generate based on topic."
        
        response = await self.invoke(
            lecture_topic=lecture_input.lecture_topic,
            lecture_text=lecture_text,
        )
        
        parsed = self._parse_translation_response(response, lecture_input.lecture_topic)
        return self._build_career_translation(parsed)
    
    def translate_sync(self, lecture_input: LectureInput) -> CareerTranslation:
        """Synchronous version of translate."""
        lecture_text = lecture_input.lecture_text or "No additional content provided. Generate based on topic."
        
        response = self.invoke_sync(
            lecture_topic=lecture_input.lecture_topic,
            lecture_text=lecture_text,
        )
        
        parsed = self._parse_translation_response(response, lecture_input.lecture_topic)
        return self._build_career_translation(parsed)
    
    def _parse_translation_response(self, response: str, topic: str) -> Dict[str, Any]:
        """Parse the LLM response into a dictionary."""
        try:
            # Try to extract JSON from the response
            # Sometimes LLM wraps JSON in markdown code blocks
            json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', response)
            if json_match:
                parsed = json.loads(json_match.group(1))
            else:
                # Try direct JSON parsing
                parsed = json.loads(response.strip())
            
            # Ensure lecture_topic is set
            if "lecture_topic" not in parsed or not parsed["lecture_topic"]:
                parsed["lecture_topic"] = topic
                
            return parsed
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse career translation response: {e}")
            logger.debug(f"Raw response: {response[:500]}...")
            default = self.get_default_response()
            default["lecture_topic"] = topic
            return default
    
    def _build_career_translation(self, parsed: Dict[str, Any]) -> CareerTranslation:
        """Build CareerTranslation model from parsed dictionary."""
        
        # Build real_world_relevance
        rwr_data = parsed.get("real_world_relevance", {})
        real_world_relevance = RealWorldRelevance(
            where_used=rwr_data.get("where_used", ["Production systems"]),
            problems_it_solves=rwr_data.get("problems_it_solves", ["Engineering challenges"]),
            risk_if_not_known=rwr_data.get("risk_if_not_known", "System issues"),
        )
        
        # Build industry_use_cases
        use_cases_data = parsed.get("industry_use_cases", [])
        industry_use_cases = []
        for uc in use_cases_data:
            if isinstance(uc, dict):
                industry_use_cases.append(IndustryUseCase(
                    domain=uc.get("domain", "Software Engineering"),
                    scenario=uc.get("scenario", "Production scenario"),
                    how_concept_is_used=uc.get("how_concept_is_used", "Applied in practice"),
                ))
        if not industry_use_cases:
            industry_use_cases = [IndustryUseCase(
                domain="Software Engineering",
                scenario="Building production systems",
                how_concept_is_used="Applied in daily engineering work"
            )]
        
        # Build company_style_tasks
        tasks_data = parsed.get("company_style_tasks", [])
        company_style_tasks = []
        for task in tasks_data:
            if isinstance(task, dict):
                company_style_tasks.append(CompanyStyleTask(
                    task_title=task.get("task_title", "Engineering Task"),
                    company_context=task.get("company_context", "Tech company"),
                    your_mission=task.get("your_mission", "Complete the task"),
                    constraints=task.get("constraints", ["Time: 4 hours"]),
                    expected_output=task.get("expected_output", "Working solution"),
                ))
        if not company_style_tasks:
            company_style_tasks = [CompanyStyleTask(
                task_title="Apply Concept",
                company_context="Engineering team",
                your_mission="Implement the concept",
                constraints=["4 hours"],
                expected_output="Working code"
            )]
        
        # Build skills_built
        skills_data = parsed.get("skills_built", {})
        skills_built = SkillsBuilt(
            technical=skills_data.get("technical", ["Technical skill"]),
            engineering_thinking=skills_data.get("engineering_thinking", ["Systems thinking"]),
            problem_solving=skills_data.get("problem_solving", ["Problem solving"]),
            team_relevance=skills_data.get("team_relevance", ["Team collaboration"]),
        )
        
        # Build career_impact
        impact_data = parsed.get("career_impact", {})
        career_impact = CareerImpact(
            relevant_roles=impact_data.get("relevant_roles", ["Software Engineer"]),
            interview_relevance=impact_data.get("interview_relevance", "Common interview topic"),
            junior_vs_senior_difference=impact_data.get("junior_vs_senior_difference", "Seniors have deeper understanding"),
        )
        
        # Build advanced_challenge
        challenge_data = parsed.get("advanced_challenge", {})
        advanced_challenge = AdvancedChallenge(
            title=challenge_data.get("title", "Advanced Challenge"),
            description=challenge_data.get("description", "Scale and optimize the solution"),
        )
        
        return CareerTranslation(
            lecture_topic=parsed.get("lecture_topic", "Unknown Topic"),
            real_world_relevance=real_world_relevance,
            industry_use_cases=industry_use_cases,
            company_style_tasks=company_style_tasks,
            skills_built=skills_built,
            career_impact=career_impact,
            advanced_challenge=advanced_challenge,
        )


# Singleton instance for reuse
_career_translator_instance: CareerTranslatorAgent | None = None


def get_career_translator() -> CareerTranslatorAgent:
    """Get or create the CareerTranslatorAgent singleton."""
    global _career_translator_instance
    if _career_translator_instance is None:
        _career_translator_instance = CareerTranslatorAgent()
    return _career_translator_instance
