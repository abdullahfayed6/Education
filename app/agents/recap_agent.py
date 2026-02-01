"""Recap Agent - Provides perfect summaries and learning tracks for lectures."""
from __future__ import annotations

import json
import logging
from typing import Any, Dict

from app.agents.base_agent import BaseInterviewAgent
from app.agents.recap_prompts import RECAP_AGENT_PROMPT
from app.models.recap_schemas import (
    RecapResponse,
    LectureSummary,
    KeyConcept,
    StudyTip,
    LearningTrack,
    PracticeExercise,
    LearningMilestone,
    LearningResource,
    QuickReference,
    QuickFormula,
    Flashcard,
    RecapInput,
)

logger = logging.getLogger(__name__)


class RecapAgent(BaseInterviewAgent):
    """
    Educational Coach AI that provides comprehensive lecture recaps.
    
    Features:
    - Perfect summaries with key concepts and takeaways
    - Study tips and learning strategies
    - Multiple learning tracks (quick review, deep understanding, practical)
    - Practice exercises and milestones
    - Quick reference materials (formulas, flashcards, cheat sheets)
    """
    
    def __init__(self, **kwargs):
        super().__init__(temperature=0.6, **kwargs)
    
    def get_prompt_template(self) -> str:
        return RECAP_AGENT_PROMPT
    
    def get_default_response(self) -> Dict[str, Any]:
        """Return a default response structure."""
        return {
            "summary": {
                "title": "Topic Summary",
                "one_liner": "Unable to generate summary",
                "overview": "Please try again with more details.",
                "key_concepts": [],
                "key_takeaways": [],
                "common_misconceptions": [],
                "prerequisites": []
            },
            "study_tips": [],
            "learning_tracks": [],
            "practice_exercises": [],
            "milestones": [],
            "resources": [],
            "quick_reference": {
                "formulas": [],
                "flashcards": [],
                "cheat_sheet": []
            },
            "difficulty_level": "intermediate",
            "estimated_study_time": "Unknown",
            "next_topics": []
        }
    
    async def generate_recap(self, recap_input: RecapInput) -> RecapResponse:
        """
        Generate a comprehensive recap for a lecture/topic.
        
        Args:
            recap_input: The input containing topic, content, and preferences
            
        Returns:
            RecapResponse with summary and learning tracks
        """
        try:
            response = await self.invoke(
                topic=recap_input.topic,
                lecture_content=recap_input.lecture_content or "Not provided",
                student_level=recap_input.student_level,
                focus_area=recap_input.focus_area or "General understanding"
            )
            
            parsed = self.parse_json_response(response)
            return self._build_recap_response(parsed, recap_input.topic)
            
        except Exception as e:
            logger.error(f"Error generating recap: {e}")
            raise
    
    def generate_recap_sync(self, recap_input: RecapInput) -> RecapResponse:
        """Synchronous version of generate_recap."""
        try:
            response = self.invoke_sync(
                topic=recap_input.topic,
                lecture_content=recap_input.lecture_content or "Not provided",
                student_level=recap_input.student_level,
                focus_area=recap_input.focus_area or "General understanding"
            )
            
            parsed = self.parse_json_response(response)
            return self._build_recap_response(parsed, recap_input.topic)
            
        except Exception as e:
            logger.error(f"Error generating recap: {e}")
            raise
    
    def _build_recap_response(self, data: Dict[str, Any], topic: str) -> RecapResponse:
        """Build a RecapResponse from parsed JSON data."""
        
        # Build summary
        summary_data = data.get("summary", {})
        key_concepts = [
            KeyConcept(
                name=c.get("name", "Concept"),
                definition=c.get("definition", ""),
                importance=c.get("importance", ""),
                example=c.get("example")
            )
            for c in summary_data.get("key_concepts", [])
        ]
        
        summary = LectureSummary(
            title=summary_data.get("title", topic),
            one_liner=summary_data.get("one_liner", f"Understanding {topic}"),
            overview=summary_data.get("overview", ""),
            key_concepts=key_concepts,
            key_takeaways=summary_data.get("key_takeaways", []),
            common_misconceptions=summary_data.get("common_misconceptions", []),
            prerequisites=summary_data.get("prerequisites", [])
        )
        
        # Build study tips
        study_tips = [
            StudyTip(
                tip=t.get("tip", ""),
                category=t.get("category", "general"),
                icon=t.get("icon", "💡")
            )
            for t in data.get("study_tips", [])
        ]
        
        # Build learning tracks
        learning_tracks = [
            LearningTrack(
                track_name=t.get("track_name", "Learning Track"),
                description=t.get("description", ""),
                duration=t.get("duration", "Unknown"),
                difficulty=t.get("difficulty", "intermediate"),
                steps=t.get("steps", []),
                icon=t.get("icon", "🛤️")
            )
            for t in data.get("learning_tracks", [])
        ]
        
        # Build practice exercises
        practice_exercises = [
            PracticeExercise(
                title=e.get("title", "Exercise"),
                description=e.get("description", ""),
                difficulty=e.get("difficulty", "medium"),
                estimated_time=e.get("estimated_time", "15 minutes"),
                skills_practiced=e.get("skills_practiced", [])
            )
            for e in data.get("practice_exercises", [])
        ]
        
        # Build milestones
        milestones = [
            LearningMilestone(
                milestone=m.get("milestone", ""),
                check_yourself=m.get("check_yourself", ""),
                icon=m.get("icon", "✅")
            )
            for m in data.get("milestones", [])
        ]
        
        # Build resources
        resources = [
            LearningResource(
                type=r.get("type", "article"),
                title=r.get("title", "Resource"),
                description=r.get("description", ""),
                difficulty=r.get("difficulty", "intermediate"),
                icon=r.get("icon", "📚")
            )
            for r in data.get("resources", [])
        ]
        
        # Build quick reference
        qr_data = data.get("quick_reference", {})
        quick_reference = QuickReference(
            formulas=[
                QuickFormula(
                    name=f.get("name", ""),
                    formula=f.get("formula", ""),
                    when_to_use=f.get("when_to_use", "")
                )
                for f in qr_data.get("formulas", [])
            ],
            flashcards=[
                Flashcard(
                    front=fc.get("front", ""),
                    back=fc.get("back", "")
                )
                for fc in qr_data.get("flashcards", [])
            ],
            cheat_sheet=qr_data.get("cheat_sheet", [])
        )
        
        return RecapResponse(
            summary=summary,
            study_tips=study_tips,
            learning_tracks=learning_tracks,
            practice_exercises=practice_exercises,
            milestones=milestones,
            resources=resources,
            quick_reference=quick_reference,
            difficulty_level=data.get("difficulty_level", "intermediate"),
            estimated_study_time=data.get("estimated_study_time", "2-3 hours"),
            next_topics=data.get("next_topics", [])
        )
