"""
Work Recommendation Agent Schemas

Data models for job and freelance opportunity recommendations.
"""

from typing import List, Optional, Dict
from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime


# ============================================
# Enums
# ============================================

class SkillLevel(str, Enum):
    """Student skill level."""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class WorkReadiness(str, Enum):
    """Work readiness level."""
    PRACTICE_FIRST = "practice_first"
    FREELANCE_READY = "freelance_ready"
    INTERNSHIP_READY = "internship_ready"
    JUNIOR_READY = "junior_ready"


class JobDifficulty(str, Enum):
    """Job entry difficulty."""
    EASY = "easy_entry"
    MEDIUM = "medium"
    HARD = "hard"


# ============================================
# Input Models
# ============================================

class StudentWorkProfile(BaseModel):
    """Student's profile for work recommendations."""
    career_goal: str = Field(..., description="Career goal", example="Become a Data Scientist")
    current_level: SkillLevel = Field(default=SkillLevel.BEGINNER)
    field_of_interest: str = Field(..., description="Main field", example="Machine Learning")
    skills: List[str] = Field(default_factory=list, example=["Python", "SQL", "Pandas"])
    tools_known: List[str] = Field(default_factory=list, example=["VS Code", "Git", "Jupyter"])
    projects_done: List[str] = Field(
        default_factory=list, 
        example=["Data Analysis Project", "Simple ML Model"]
    )
    available_hours_per_week: float = Field(default=20, ge=5, le=60)


class LearningState(BaseModel):
    """Student's current learning state."""
    current_topics_learning: List[str] = Field(
        default_factory=list,
        example=["Deep Learning", "NLP"]
    )
    strong_areas: List[str] = Field(
        default_factory=list,
        example=["Data cleaning", "Python basics", "SQL queries"]
    )
    weak_areas: List[str] = Field(
        default_factory=list,
        example=["Machine Learning math", "Cloud deployment"]
    )


class WorkRecommendationInput(BaseModel):
    """Complete input for work recommendations."""
    student_profile: StudentWorkProfile
    learning_state: LearningState


# ============================================
# Output Models - Job Recommendations
# ============================================

class JobRecommendation(BaseModel):
    """A single job recommendation."""
    job_title: str = Field(..., description="Job title", example="Junior Data Analyst")
    job_type: str = Field(default="internship", description="internship, junior, entry-level")
    why_it_fits: str = Field(..., description="Why this job fits the student")
    skills_they_have: List[str] = Field(..., description="Skills student already has")
    missing_skills: List[str] = Field(..., description="Skills to work on")
    difficulty: JobDifficulty = Field(default=JobDifficulty.MEDIUM)
    time_to_ready: str = Field(default="1-2 months", description="Time to be job-ready")
    typical_tasks: List[str] = Field(default_factory=list, description="What they'd do")
    icon: str = Field(default="💼")
    # Search URLs
    search_urls: List[Dict] = Field(
        default_factory=list,
        description="Direct links to search for this job"
    )


class FreelanceOpportunity(BaseModel):
    """A single freelance opportunity."""
    gig_type: str = Field(..., description="Type of freelance work", example="Data Cleaning")
    example_task: str = Field(..., description="Example of a real task")
    why_they_can_do_it: str = Field(..., description="Why student can handle this")
    skills_required: List[str] = Field(..., description="Skills needed")
    platform_types: List[str] = Field(
        default_factory=list,
        description="Where to find these gigs (platform types)",
        example=["Freelance marketplaces", "Job boards", "Direct clients"]
    )
    earning_potential: str = Field(default="$50-200/project", description="Typical earnings")
    difficulty: JobDifficulty = Field(default=JobDifficulty.EASY)
    icon: str = Field(default="💻")
    # Platform URLs
    platform_urls: List[Dict] = Field(
        default_factory=list,
        description="Direct links to find these gigs on platforms"
    )


class IncomeStrategy(BaseModel):
    """Income strategy advice."""
    start_freelance_now: bool = Field(..., description="Should they start freelancing now?")
    freelance_reasoning: str = Field(..., description="Why or why not")
    fast_income_path: str = Field(..., description="Best path for quick income")
    long_term_career_path: str = Field(..., description="Best long-term career path")
    recommended_first_step: str = Field(..., description="What to do first")


class SkillGap(BaseModel):
    """Skill gap analysis for work."""
    skill_name: str = Field(..., description="Skill to improve")
    importance: str = Field(..., description="Why it's important for work")
    how_to_learn: str = Field(..., description="How to learn/improve")
    time_to_learn: str = Field(..., description="Estimated time")


class HighImpactProject(BaseModel):
    """Project that increases employability."""
    project_name: str = Field(..., description="Project name")
    description: str = Field(..., description="What to build")
    skills_demonstrated: List[str] = Field(..., description="Skills it shows")
    why_employers_care: str = Field(..., description="Why this impresses employers")
    estimated_time: str = Field(..., description="Time to complete")


class WorkReadinessAnalysis(BaseModel):
    """Analysis of student's work readiness."""
    readiness_level: WorkReadiness
    readiness_summary: str = Field(..., description="Summary of readiness")
    strengths_for_work: List[str] = Field(..., description="Strengths they can leverage")
    gaps_to_address: List[str] = Field(..., description="Gaps to work on")
    recommended_path: str = Field(..., description="Recommended next steps")


# ============================================
# Main Response Model
# ============================================

class WorkRecommendationResponse(BaseModel):
    """Complete work recommendation response."""
    # Summary
    work_readiness: WorkReadinessAnalysis
    
    # Job Recommendations
    job_recommendations: List[JobRecommendation] = Field(
        ..., 
        description="3-5 suitable job types"
    )
    
    # Freelance Opportunities
    freelance_opportunities: List[FreelanceOpportunity] = Field(
        ...,
        description="3-5 freelance gig types"
    )
    
    # Strategy
    income_strategy: IncomeStrategy
    
    # Skill Gaps
    skill_gaps: List[SkillGap] = Field(
        ...,
        description="Top 3 skills to improve"
    )
    
    # High Impact Project
    high_impact_project: HighImpactProject
    
    # Metadata
    generated_at: datetime = Field(default_factory=datetime.now)
    
    # Quick Actions
    immediate_actions: List[str] = Field(
        default_factory=list,
        description="What to do this week"
    )


# ============================================
# Request Models for API
# ============================================

class QuickWorkRequest(BaseModel):
    """Simplified request for work recommendations."""
    # Required
    career_goal: str = Field(..., example="Become a Backend Developer")
    field_of_interest: str = Field(..., example="Web Development")
    skills: List[str] = Field(..., example=["Python", "JavaScript", "SQL"])
    
    # Optional with defaults
    current_level: str = Field(default="beginner")
    tools_known: List[str] = Field(default_factory=list, example=["Git", "VS Code"])
    projects_done: List[str] = Field(default_factory=list, example=["Portfolio website"])
    hours_per_week: float = Field(default=20, ge=5, le=60)
    
    # Learning state
    currently_learning: List[str] = Field(default_factory=list, example=["React", "Node.js"])
    strong_areas: List[str] = Field(default_factory=list, example=["Python basics"])
    weak_areas: List[str] = Field(default_factory=list, example=["System design"])


# ============================================
# Live Job Search Models
# ============================================

class LiveJobListing(BaseModel):
    """A live job listing from API search."""
    title: str = Field(..., description="Job title")
    company: str = Field(..., description="Company name")
    location: str = Field(default="", description="Job location")
    url: str = Field(..., description="Apply URL")
    salary: Optional[str] = Field(default=None, description="Salary info")
    description: Optional[str] = Field(default=None, description="Job description snippet")
    source: str = Field(default="unknown", description="Where this job was found")
    posted_date: Optional[str] = Field(default=None, description="When job was posted")
    job_type: Optional[str] = Field(default=None, description="Full-time, Part-time, etc.")


class JobSearchURL(BaseModel):
    """A search URL for a job board."""
    name: str = Field(..., description="Platform name", example="LinkedIn Jobs")
    url: str = Field(..., description="Search URL")
    logo: str = Field(default="🔗", description="Platform icon")


class FreelancePlatformURL(BaseModel):
    """A search URL for a freelance platform."""
    platform: str = Field(..., description="Platform name", example="Upwork")
    search_url: str = Field(..., description="Search URL with query")
    logo: str = Field(default="🔗", description="Platform icon")
    tips: Optional[str] = Field(default=None, description="Tips for this platform")


class LiveJobSearchResponse(BaseModel):
    """Response for live job search."""
    query: str = Field(..., description="Search query used")
    location: Optional[str] = Field(default=None)
    
    # Live API results
    live_jobs: List[LiveJobListing] = Field(
        default_factory=list,
        description="Jobs from live API search"
    )
    
    # Direct search URLs for all major job boards
    search_urls: List[JobSearchURL] = Field(
        default_factory=list,
        description="Direct links to search on job boards"
    )
    
    # API providers used
    providers_used: List[str] = Field(
        default_factory=list,
        description="Which APIs were used for this search"
    )
    
    # Metadata
    total_results: int = Field(default=0)
    searched_at: datetime = Field(default_factory=datetime.now)


class FreelanceSearchResponse(BaseModel):
    """Response for freelance opportunity search."""
    skills: List[str] = Field(..., description="Skills searched for")
    
    # Platform search URLs
    platforms: List[FreelancePlatformURL] = Field(
        default_factory=list,
        description="Search URLs for each platform"
    )
    
    # Organized by skill
    by_skill: Dict[str, List[Dict]] = Field(
        default_factory=dict,
        description="Platform URLs organized by skill"
    )
    
    # General tips
    tips: List[str] = Field(
        default_factory=list,
        description="Tips for finding freelance work"
    )
    
    searched_at: datetime = Field(default_factory=datetime.now)


class FullWorkSearchResponse(BaseModel):
    """Complete response with AI recommendations + live search results."""
    # AI-generated recommendations
    ai_recommendations: WorkRecommendationResponse
    
    # Live job search results
    live_jobs: LiveJobSearchResponse
    
    # Freelance platform URLs
    freelance_platforms: FreelanceSearchResponse
    
    # Combined quick links
    quick_links: Dict[str, List[Dict]] = Field(
        default_factory=dict,
        description="Quick access links organized by category"
    )
