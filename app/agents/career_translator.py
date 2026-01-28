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
    LearningAdvice,
    LectureInput,
    LifeStoryExplanation,
    PrerequisiteKnowledge,
    PrerequisiteTopic,
    ProductionChallenge,
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
            },
            "production_challenges": [
                {
                    "challenge": "Scale failure under high traffic",
                    "why_it_happens": "System not designed for load spikes",
                    "professional_solution": "Implement auto-scaling and load balancing"
                },
                {
                    "challenge": "Performance bottleneck in critical path",
                    "why_it_happens": "Unoptimized queries or algorithms",
                    "professional_solution": "Profile, optimize, and add caching layers"
                },
                {
                    "challenge": "Data quality issues in production",
                    "why_it_happens": "Edge cases not covered in testing",
                    "professional_solution": "Add data validation and monitoring"
                },
                {
                    "challenge": "System design limitation",
                    "why_it_happens": "Initial architecture didn't anticipate growth",
                    "professional_solution": "Refactor with scalable patterns"
                },
                {
                    "challenge": "Integration compatibility issues",
                    "why_it_happens": "Third-party API changes or version mismatches",
                    "professional_solution": "Use adapters and version contracts"
                },
                {
                    "challenge": "Infrastructure cost overrun",
                    "why_it_happens": "Inefficient resource utilization",
                    "professional_solution": "Implement cost monitoring and right-sizing"
                },
                {
                    "challenge": "Debugging complexity in production",
                    "why_it_happens": "Lack of observability",
                    "professional_solution": "Add structured logging and distributed tracing"
                }
            ],
            "life_story_explanation": {
                "story_title": "The Restaurant Reservation",
                "story": "Imagine you're organizing a dinner with 10 friends. You call the restaurant to make a reservation, but they need to know exactly how many people are coming. Some friends haven't confirmed yet, so you have to wait. Meanwhile, the restaurant can't prepare the right table size. Everyone is blocked waiting for information before they can proceed.",
                "concept_mapping": "Just like waiting for all friends to confirm before the restaurant can prepare, systems often need to wait for all data or dependencies before processing. This is the core of synchronization and blocking operations in software."
            },
            "prerequisite_knowledge": {
                "why_prerequisites_matter": "Without these foundations, learners will struggle to understand the core concepts and make avoidable mistakes in production.",
                "required_topics": [
                    {
                        "topic": "Basic Programming Fundamentals",
                        "why_needed": "Core syntax and logic flow are essential for understanding implementation",
                        "risk_if_missing": "Unable to read or write code examples, complete confusion"
                    },
                    {
                        "topic": "Data Structures Basics",
                        "why_needed": "Understanding how data is organized is fundamental to most concepts",
                        "risk_if_missing": "Cannot understand performance implications or design choices"
                    },
                    {
                        "topic": "Algorithm Complexity (Big O)",
                        "why_needed": "Required to understand why certain approaches are better",
                        "risk_if_missing": "Will write inefficient code without knowing why"
                    },
                    {
                        "topic": "Problem Decomposition",
                        "why_needed": "Breaking problems into smaller parts is essential for implementation",
                        "risk_if_missing": "Overwhelmed by complexity, unable to start solving"
                    },
                    {
                        "topic": "Basic Debugging Skills",
                        "why_needed": "Needed to verify understanding through experimentation",
                        "risk_if_missing": "Cannot troubleshoot when things don't work as expected"
                    }
                ]
            },
            "learning_success_advice": [
                {
                    "advice_title": "Build before you read",
                    "what_to_do": "Try implementing a basic version before reading all the theory",
                    "why_this_matters": "Active struggle creates deeper understanding than passive reading",
                    "common_mistake_to_avoid": "Reading everything first and never actually coding"
                },
                {
                    "advice_title": "Break it, then fix it",
                    "what_to_do": "Intentionally introduce bugs to see how the system fails",
                    "why_this_matters": "Understanding failure modes builds debugging intuition",
                    "common_mistake_to_avoid": "Only running happy-path examples"
                },
                {
                    "advice_title": "Explain it simply",
                    "what_to_do": "Try explaining the concept to someone non-technical",
                    "why_this_matters": "If you can't explain it simply, you don't understand it deeply",
                    "common_mistake_to_avoid": "Memorizing jargon without understanding meaning"
                },
                {
                    "advice_title": "Connect to real systems",
                    "what_to_do": "Research which companies use this and how",
                    "why_this_matters": "Real-world context makes abstract concepts concrete",
                    "common_mistake_to_avoid": "Studying in isolation from actual applications"
                },
                {
                    "advice_title": "Practice under constraints",
                    "what_to_do": "Solve problems with time limits and without looking up answers",
                    "why_this_matters": "Interview and work conditions require recall, not lookup",
                    "common_mistake_to_avoid": "Always coding with documentation open"
                },
                {
                    "advice_title": "Draw it out",
                    "what_to_do": "Create diagrams and visualizations of the concept",
                    "why_this_matters": "Visual representation reveals structure and relationships",
                    "common_mistake_to_avoid": "Keeping everything as text in your head"
                },
                {
                    "advice_title": "Ask why, not just how",
                    "what_to_do": "For each technique, understand why it's designed that way",
                    "why_this_matters": "Understanding rationale helps you adapt to new situations",
                    "common_mistake_to_avoid": "Memorizing patterns without understanding trade-offs"
                },
                {
                    "advice_title": "Compare alternatives",
                    "what_to_do": "Study what other approaches exist and their trade-offs",
                    "why_this_matters": "Engineers make decisions by comparing options",
                    "common_mistake_to_avoid": "Learning one solution as 'the' answer"
                },
                {
                    "advice_title": "Teach to learn",
                    "what_to_do": "Write a blog post or create a tutorial about the topic",
                    "why_this_matters": "Teaching forces you to fill gaps in understanding",
                    "common_mistake_to_avoid": "Passive consumption without production"
                },
                {
                    "advice_title": "Test your understanding",
                    "what_to_do": "Solve new problems without templates or examples",
                    "why_this_matters": "True mastery means applying knowledge to novel situations",
                    "common_mistake_to_avoid": "Feeling confident after following tutorials"
                }
            ]
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
        
        # Build production_challenges
        prod_challenges_data = parsed.get("production_challenges", [])
        production_challenges = []
        for pc in prod_challenges_data:
            if isinstance(pc, dict):
                production_challenges.append(ProductionChallenge(
                    challenge=pc.get("challenge", "Production issue"),
                    why_it_happens=pc.get("why_it_happens", "System complexity"),
                    professional_solution=pc.get("professional_solution", "Engineering best practices"),
                ))
        # Ensure we have at least some default production challenges
        if not production_challenges:
            production_challenges = [
                ProductionChallenge(
                    challenge="Scale failure under high traffic",
                    why_it_happens="System not designed for load spikes",
                    professional_solution="Implement auto-scaling and load balancing"
                ),
                ProductionChallenge(
                    challenge="Performance bottleneck",
                    why_it_happens="Unoptimized code paths",
                    professional_solution="Profile and optimize critical sections"
                ),
                ProductionChallenge(
                    challenge="Data quality issues",
                    why_it_happens="Edge cases in production data",
                    professional_solution="Add validation and monitoring"
                ),
                ProductionChallenge(
                    challenge="System design limitation",
                    why_it_happens="Architecture didn't anticipate growth",
                    professional_solution="Refactor with scalable patterns"
                ),
                ProductionChallenge(
                    challenge="Integration issues",
                    why_it_happens="Third-party API changes",
                    professional_solution="Use adapters and version contracts"
                ),
                ProductionChallenge(
                    challenge="Infrastructure cost overrun",
                    why_it_happens="Inefficient resource usage",
                    professional_solution="Implement cost monitoring"
                ),
                ProductionChallenge(
                    challenge="Debugging complexity",
                    why_it_happens="Lack of observability",
                    professional_solution="Add structured logging and tracing"
                ),
            ]
        
        # Build life_story_explanation
        story_data = parsed.get("life_story_explanation", {})
        life_story_explanation = LifeStoryExplanation(
            story_title=story_data.get("story_title", "Understanding Through Real Life"),
            story=story_data.get("story", "Imagine organizing a group activity where everyone needs to coordinate and wait for each other before proceeding. This everyday scenario mirrors how systems work together."),
            concept_mapping=story_data.get("concept_mapping", "The story elements directly map to the technical concept, helping you understand the intuition behind the engineering principles."),
        )
        
        # Build prerequisite_knowledge
        prereq_data = parsed.get("prerequisite_knowledge", {})
        required_topics_data = prereq_data.get("required_topics", [])
        required_topics = []
        for topic in required_topics_data:
            if isinstance(topic, dict):
                required_topics.append(PrerequisiteTopic(
                    topic=topic.get("topic", "Foundational Topic"),
                    why_needed=topic.get("why_needed", "Required for understanding"),
                    risk_if_missing=topic.get("risk_if_missing", "Confusion and errors"),
                ))
        # Ensure we have at least some default prerequisites
        if not required_topics:
            required_topics = [
                PrerequisiteTopic(
                    topic="Basic Programming Fundamentals",
                    why_needed="Core syntax and logic flow are essential",
                    risk_if_missing="Unable to read or write code examples"
                ),
                PrerequisiteTopic(
                    topic="Data Structures Basics",
                    why_needed="Understanding data organization is fundamental",
                    risk_if_missing="Cannot understand performance implications"
                ),
                PrerequisiteTopic(
                    topic="Algorithm Complexity (Big O)",
                    why_needed="Required to understand efficiency trade-offs",
                    risk_if_missing="Will write inefficient code"
                ),
                PrerequisiteTopic(
                    topic="Problem Decomposition",
                    why_needed="Breaking problems into parts is essential",
                    risk_if_missing="Overwhelmed by complexity"
                ),
                PrerequisiteTopic(
                    topic="Basic Debugging Skills",
                    why_needed="Needed to verify understanding",
                    risk_if_missing="Cannot troubleshoot issues"
                ),
            ]
        
        prerequisite_knowledge = PrerequisiteKnowledge(
            why_prerequisites_matter=prereq_data.get(
                "why_prerequisites_matter",
                "Without these foundations, learners will struggle to understand core concepts and make avoidable production mistakes."
            ),
            required_topics=required_topics,
        )
        
        # Build learning_success_advice
        advice_data = parsed.get("learning_success_advice", [])
        learning_success_advice = []
        for advice in advice_data:
            if isinstance(advice, dict):
                learning_success_advice.append(LearningAdvice(
                    advice_title=advice.get("advice_title", "Learning Tip"),
                    what_to_do=advice.get("what_to_do", "Practice the concept"),
                    why_this_matters=advice.get("why_this_matters", "Improves understanding"),
                    common_mistake_to_avoid=advice.get("common_mistake_to_avoid", "Passive learning"),
                ))
        # Ensure we have at least some default advice
        if not learning_success_advice:
            learning_success_advice = [
                LearningAdvice(
                    advice_title="Build before you read",
                    what_to_do="Try implementing before reading all theory",
                    why_this_matters="Active struggle creates deeper understanding",
                    common_mistake_to_avoid="Reading everything first without coding"
                ),
                LearningAdvice(
                    advice_title="Break it, then fix it",
                    what_to_do="Intentionally introduce bugs to see failures",
                    why_this_matters="Understanding failure builds debugging intuition",
                    common_mistake_to_avoid="Only running happy-path examples"
                ),
                LearningAdvice(
                    advice_title="Explain it simply",
                    what_to_do="Explain the concept to a non-technical person",
                    why_this_matters="Simple explanation proves deep understanding",
                    common_mistake_to_avoid="Memorizing jargon without meaning"
                ),
                LearningAdvice(
                    advice_title="Connect to real systems",
                    what_to_do="Research which companies use this and how",
                    why_this_matters="Real-world context makes concepts concrete",
                    common_mistake_to_avoid="Studying in isolation"
                ),
                LearningAdvice(
                    advice_title="Practice under constraints",
                    what_to_do="Solve problems with time limits",
                    why_this_matters="Interviews require recall, not lookup",
                    common_mistake_to_avoid="Always coding with docs open"
                ),
                LearningAdvice(
                    advice_title="Draw it out",
                    what_to_do="Create diagrams and visualizations",
                    why_this_matters="Visual representation reveals structure",
                    common_mistake_to_avoid="Keeping everything as text"
                ),
                LearningAdvice(
                    advice_title="Ask why, not just how",
                    what_to_do="Understand why techniques are designed that way",
                    why_this_matters="Rationale helps adapt to new situations",
                    common_mistake_to_avoid="Memorizing without understanding trade-offs"
                ),
                LearningAdvice(
                    advice_title="Compare alternatives",
                    what_to_do="Study other approaches and their trade-offs",
                    why_this_matters="Engineers decide by comparing options",
                    common_mistake_to_avoid="Learning one solution as 'the' answer"
                ),
                LearningAdvice(
                    advice_title="Teach to learn",
                    what_to_do="Write a blog post or tutorial about the topic",
                    why_this_matters="Teaching forces you to fill gaps",
                    common_mistake_to_avoid="Passive consumption without production"
                ),
                LearningAdvice(
                    advice_title="Test your understanding",
                    what_to_do="Solve new problems without templates",
                    why_this_matters="True mastery means applying to novel situations",
                    common_mistake_to_avoid="Feeling confident after tutorials"
                ),
            ]
        
        return CareerTranslation(
            lecture_topic=parsed.get("lecture_topic", "Unknown Topic"),
            real_world_relevance=real_world_relevance,
            industry_use_cases=industry_use_cases,
            company_style_tasks=company_style_tasks,
            skills_built=skills_built,
            career_impact=career_impact,
            advanced_challenge=advanced_challenge,
            production_challenges=production_challenges,
            life_story_explanation=life_story_explanation,
            prerequisite_knowledge=prerequisite_knowledge,
            learning_success_advice=learning_success_advice,
        )


# Singleton instance for reuse
_career_translator_instance: CareerTranslatorAgent | None = None


def get_career_translator() -> CareerTranslatorAgent:
    """Get or create the CareerTranslatorAgent singleton."""
    global _career_translator_instance
    if _career_translator_instance is None:
        _career_translator_instance = CareerTranslatorAgent()
    return _career_translator_instance
