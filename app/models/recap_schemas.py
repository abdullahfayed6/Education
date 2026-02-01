"""Schemas for the Recap Agent - Summary and Learning Tracks."""
from __future__ import annotations

from typing import List, Optional
from pydantic import BaseModel, Field


# ============================================
# Summary Models
# ============================================

class KeyConcept(BaseModel):
    """A key concept from the lecture."""
    name: str = Field(..., description="Name of the concept")
    definition: str = Field(..., description="Clear, concise definition")
    importance: str = Field(..., description="Why this concept matters")
    example: Optional[str] = Field(None, description="Simple example to illustrate")


class LectureSummary(BaseModel):
    """Comprehensive summary of the lecture."""
    title: str = Field(..., description="Topic/Lecture title")
    one_liner: str = Field(..., description="One sentence summary of the entire topic")
    overview: str = Field(..., description="2-3 paragraph comprehensive overview")
    key_concepts: List[KeyConcept] = Field(default_factory=list, description="Main concepts covered")
    key_takeaways: List[str] = Field(default_factory=list, description="Main points to remember")
    common_misconceptions: List[str] = Field(default_factory=list, description="Things students often get wrong")
    prerequisites: List[str] = Field(default_factory=list, description="What you should know before this topic")


# ============================================
# Learning Track Models
# ============================================

class StudyTip(BaseModel):
    """A study tip for the topic."""
    tip: str = Field(..., description="The study tip")
    category: str = Field(..., description="Category: memorization, understanding, practice, etc.")
    icon: str = Field(default="💡", description="Icon for the tip")


class LearningResource(BaseModel):
    """A learning resource recommendation."""
    type: str = Field(..., description="Type: video, article, book, course, tool")
    title: str = Field(..., description="Resource title or name")
    description: str = Field(..., description="What you'll learn from this")
    difficulty: str = Field(default="intermediate", description="beginner, intermediate, advanced")
    icon: str = Field(default="📚", description="Icon for resource type")


class PracticeExercise(BaseModel):
    """A practice exercise to reinforce learning."""
    title: str = Field(..., description="Exercise title")
    description: str = Field(..., description="What to do")
    difficulty: str = Field(..., description="easy, medium, hard")
    estimated_time: str = Field(..., description="Time to complete")
    skills_practiced: List[str] = Field(default_factory=list, description="Skills you'll practice")


class LearningMilestone(BaseModel):
    """A milestone in the learning journey."""
    milestone: str = Field(..., description="What you should be able to do")
    check_yourself: str = Field(..., description="How to verify you've achieved this")
    icon: str = Field(default="✅", description="Icon for the milestone")


class LearningTrack(BaseModel):
    """A structured learning path for the topic."""
    track_name: str = Field(..., description="Name of the learning track")
    description: str = Field(..., description="What this track covers")
    duration: str = Field(..., description="Estimated time to complete")
    difficulty: str = Field(..., description="beginner, intermediate, advanced")
    steps: List[str] = Field(default_factory=list, description="Ordered steps to follow")
    icon: str = Field(default="🛤️", description="Icon for the track")


# ============================================
# Quick Reference Models
# ============================================

class QuickFormula(BaseModel):
    """A formula or syntax to remember."""
    name: str = Field(..., description="Name of the formula/syntax")
    formula: str = Field(..., description="The actual formula or syntax")
    when_to_use: str = Field(..., description="When to apply this")


class Flashcard(BaseModel):
    """A flashcard for quick review."""
    front: str = Field(..., description="Question or term")
    back: str = Field(..., description="Answer or definition")


class QuickReference(BaseModel):
    """Quick reference materials."""
    formulas: List[QuickFormula] = Field(default_factory=list, description="Key formulas/syntax")
    flashcards: List[Flashcard] = Field(default_factory=list, description="Flashcards for review")
    cheat_sheet: List[str] = Field(default_factory=list, description="Quick facts to remember")


# ============================================
# Main Recap Response Model
# ============================================

class RecapResponse(BaseModel):
    """Complete recap response with summary and learning tracks."""
    
    # Summary Section
    summary: LectureSummary = Field(..., description="Comprehensive lecture summary")
    
    # Learning Tracks Section
    study_tips: List[StudyTip] = Field(default_factory=list, description="Tips for studying this topic")
    learning_tracks: List[LearningTrack] = Field(default_factory=list, description="Different learning paths")
    practice_exercises: List[PracticeExercise] = Field(default_factory=list, description="Exercises to practice")
    milestones: List[LearningMilestone] = Field(default_factory=list, description="Learning milestones to achieve")
    
    # Resources Section
    resources: List[LearningResource] = Field(default_factory=list, description="Recommended resources")
    
    # Quick Reference Section
    quick_reference: QuickReference = Field(default_factory=QuickReference, description="Quick reference materials")
    
    # Metadata
    difficulty_level: str = Field(default="intermediate", description="Overall topic difficulty")
    estimated_study_time: str = Field(default="2-3 hours", description="Time to master this topic")
    next_topics: List[str] = Field(default_factory=list, description="What to learn next")


# ============================================
# Input Model
# ============================================

class RecapInput(BaseModel):
    """Input for the recap agent."""
    topic: str = Field(..., description="The lecture topic or subject")
    lecture_content: Optional[str] = Field(None, description="Optional: lecture notes or content")
    student_level: str = Field(default="intermediate", description="Student level: beginner, intermediate, advanced")
    focus_area: Optional[str] = Field(None, description="Optional: specific area to focus on")
