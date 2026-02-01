"""API endpoints for the Recap Agent - Summary and Learning Tracks."""
from __future__ import annotations

import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional

from app.agents.recap_agent import RecapAgent
from app.models.recap_schemas import RecapResponse, RecapInput

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/recap", tags=["Recap - Summary & Learning Tracks"])


class RecapRequest(BaseModel):
    """Request model for recap generation."""
    topic: str = Field(..., description="The lecture topic or subject to recap", example="Binary Search Trees")
    lecture_content: Optional[str] = Field(
        None, 
        description="Optional lecture notes or content for more accurate recap",
        example="Today we covered BST operations: insertion, deletion, and traversal..."
    )
    student_level: str = Field(
        default="intermediate",
        description="Student's level: beginner, intermediate, or advanced",
        example="intermediate"
    )
    focus_area: Optional[str] = Field(
        None,
        description="Optional specific area to focus on",
        example="Understanding time complexity"
    )


@router.post(
    "/generate",
    response_model=RecapResponse,
    summary="Generate Lecture Recap",
    description="""
## Generate a comprehensive lecture recap with:

### 📝 Perfect Summary
- One-liner summary
- Comprehensive overview
- Key concepts with definitions
- Main takeaways
- Common misconceptions

### 💡 Study Tips
- Actionable study advice
- Categorized by type (memorization, understanding, practice)

### 🛤️ Learning Tracks
- **Quick Review**: 30-60 min refresher
- **Deep Understanding**: Thorough mastery
- **Practical Application**: Hands-on learning

### 📚 Additional Resources
- Practice exercises with difficulty levels
- Learning milestones to track progress
- Recommended resources (videos, articles, books)
- Quick reference (formulas, flashcards, cheat sheet)
"""
)
async def generate_recap(request: RecapRequest) -> RecapResponse:
    """
    Generate a comprehensive recap for a lecture or topic.
    
    This endpoint provides:
    - Perfect summaries with key concepts
    - Multiple learning tracks
    - Study tips and strategies
    - Practice exercises
    - Quick reference materials
    """
    try:
        agent = RecapAgent()
        
        recap_input = RecapInput(
            topic=request.topic,
            lecture_content=request.lecture_content,
            student_level=request.student_level,
            focus_area=request.focus_area
        )
        
        result = await agent.generate_recap(recap_input)
        
        logger.info(f"Successfully generated recap for: {request.topic}")
        return result
        
    except Exception as e:
        logger.error(f"Error generating recap: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate recap: {str(e)}"
        )


@router.post(
    "/quick-summary",
    summary="Get Quick Summary Only",
    description="Get just the summary section without learning tracks"
)
async def get_quick_summary(request: RecapRequest):
    """Get a quick summary of the topic without full learning tracks."""
    try:
        agent = RecapAgent()
        
        recap_input = RecapInput(
            topic=request.topic,
            lecture_content=request.lecture_content,
            student_level=request.student_level,
            focus_area=request.focus_area
        )
        
        result = await agent.generate_recap(recap_input)
        
        return {
            "topic": request.topic,
            "summary": result.summary,
            "difficulty_level": result.difficulty_level,
            "estimated_study_time": result.estimated_study_time
        }
        
    except Exception as e:
        logger.error(f"Error generating quick summary: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate summary: {str(e)}"
        )


@router.post(
    "/study-plan",
    summary="Get Study Plan Only",
    description="Get learning tracks and study tips without full summary"
)
async def get_study_plan(request: RecapRequest):
    """Get a focused study plan with tracks, tips, and exercises."""
    try:
        agent = RecapAgent()
        
        recap_input = RecapInput(
            topic=request.topic,
            lecture_content=request.lecture_content,
            student_level=request.student_level,
            focus_area=request.focus_area
        )
        
        result = await agent.generate_recap(recap_input)
        
        return {
            "topic": request.topic,
            "study_tips": result.study_tips,
            "learning_tracks": result.learning_tracks,
            "practice_exercises": result.practice_exercises,
            "milestones": result.milestones,
            "resources": result.resources
        }
        
    except Exception as e:
        logger.error(f"Error generating study plan: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate study plan: {str(e)}"
        )


@router.post(
    "/flashcards",
    summary="Get Flashcards",
    description="Get quick reference flashcards for review"
)
async def get_flashcards(request: RecapRequest):
    """Get flashcards and cheat sheet for quick review."""
    try:
        agent = RecapAgent()
        
        recap_input = RecapInput(
            topic=request.topic,
            lecture_content=request.lecture_content,
            student_level=request.student_level,
            focus_area=request.focus_area
        )
        
        result = await agent.generate_recap(recap_input)
        
        return {
            "topic": request.topic,
            "quick_reference": result.quick_reference,
            "key_concepts": result.summary.key_concepts,
            "key_takeaways": result.summary.key_takeaways
        }
        
    except Exception as e:
        logger.error(f"Error generating flashcards: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate flashcards: {str(e)}"
        )
