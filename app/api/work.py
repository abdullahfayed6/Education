"""API endpoints for the Work Recommendation Agent."""
from __future__ import annotations

import logging
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.agents.work_agent import WorkRecommendationAgent
from app.models.work_schemas import (
    WorkRecommendationInput,
    WorkRecommendationResponse,
    QuickWorkRequest,
    StudentWorkProfile,
    LearningState,
    SkillLevel,
    JobRecommendation,
    FreelanceOpportunity,
    LiveJobSearchResponse,
    FreelanceSearchResponse,
    FullWorkSearchResponse
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/work", tags=["Work Recommendations - Jobs & Freelance"])


# ============================================
# Request Models
# ============================================

class SimpleWorkRequest(BaseModel):
    """Simplified request for work recommendations."""
    # Required
    career_goal: str = Field(..., example="Become a Data Scientist")
    field_of_interest: str = Field(..., example="Machine Learning")
    skills: List[str] = Field(..., example=["Python", "SQL", "Pandas", "NumPy"])
    
    # Optional with defaults
    current_level: str = Field(default="beginner", example="intermediate")
    tools_known: List[str] = Field(default_factory=list, example=["Git", "VS Code", "Jupyter"])
    projects_done: List[str] = Field(default_factory=list, example=["Titanic ML Project"])
    hours_per_week: float = Field(default=20, ge=5, le=60)
    
    # Learning state
    currently_learning: List[str] = Field(default_factory=list, example=["Deep Learning"])
    strong_areas: List[str] = Field(default_factory=list, example=["Data cleaning", "Python"])
    weak_areas: List[str] = Field(default_factory=list, example=["Statistics", "Deployment"])


class QuickJobsRequest(BaseModel):
    """Quick request for job recommendations only."""
    skills: List[str] = Field(..., example=["Python", "JavaScript", "React"])
    career_goal: str = Field(..., example="Frontend Developer")
    current_level: str = Field(default="beginner")


class FreelanceRequest(BaseModel):
    """Request for freelance opportunities only."""
    skills: List[str] = Field(..., example=["Python", "SQL", "Excel"])
    tools_known: List[str] = Field(default_factory=list, example=["Pandas", "Jupyter"])
    projects_done: List[str] = Field(default_factory=list)
    hours_per_week: float = Field(default=15, ge=5, le=40)
    current_level: str = Field(default="beginner")


class LiveJobSearchRequest(BaseModel):
    """Request for live job search."""
    keywords: List[str] = Field(..., example=["Python Developer", "Junior"])
    location: str = Field(default="", example="New York")
    job_type: str = Field(default="", example="internship")  # internship, junior, entry
    limit: int = Field(default=10, ge=1, le=50)


class FreelanceURLsRequest(BaseModel):
    """Request for freelance platform URLs."""
    skills: List[str] = Field(..., example=["Python", "Web Scraping", "Data Analysis"])
    gig_types: List[str] = Field(default_factory=list, example=["Data Cleaning", "Automation"])


class FullSearchRequest(BaseModel):
    """Request for full search with AI + live jobs + freelance."""
    # Profile
    career_goal: str = Field(..., example="Become a Data Scientist")
    field_of_interest: str = Field(..., example="Machine Learning")
    skills: List[str] = Field(..., example=["Python", "SQL", "Pandas"])
    current_level: str = Field(default="beginner")
    tools_known: List[str] = Field(default_factory=list)
    projects_done: List[str] = Field(default_factory=list)
    hours_per_week: float = Field(default=20)
    
    # Learning state
    currently_learning: List[str] = Field(default_factory=list)
    strong_areas: List[str] = Field(default_factory=list)
    weak_areas: List[str] = Field(default_factory=list)
    
    # Search options
    location: str = Field(default="", example="Remote")


# ============================================
# Main Endpoints
# ============================================

@router.post(
    "/recommendations",
    response_model=WorkRecommendationResponse,
    summary="Get Job & Freelance Recommendations",
    description="""
## Get personalized job and freelance recommendations

### What you'll receive:

🔍 **Work Readiness Analysis**
- Your current readiness level
- Strengths for work
- Gaps to address
- Recommended path

💼 **Job Recommendations (3-5)**
- Suitable job titles
- Why each fits your profile
- Skills you have and missing
- Difficulty level
- Time to be ready

💻 **Freelance Opportunities (3-5)**
- Gig types you can do NOW
- Example tasks
- Earning potential
- Where to find clients

🚀 **Income Strategy**
- Start freelance now or skill up?
- Fast income path
- Long-term career path

📈 **Skill Gaps**
- Top 3 skills to unlock better work
- How to learn each

🎯 **High-Impact Project**
- One project to boost employability

### The advice is:
- Realistic for your level
- Focused on 1-3 month timeline
- Practical, not motivational
"""
)
async def get_work_recommendations(request: SimpleWorkRequest) -> WorkRecommendationResponse:
    """Get comprehensive job and freelance recommendations."""
    try:
        agent = WorkRecommendationAgent()
        
        # Convert to QuickWorkRequest
        quick_request = QuickWorkRequest(
            career_goal=request.career_goal,
            field_of_interest=request.field_of_interest,
            skills=request.skills,
            current_level=request.current_level,
            tools_known=request.tools_known,
            projects_done=request.projects_done,
            hours_per_week=request.hours_per_week,
            currently_learning=request.currently_learning,
            strong_areas=request.strong_areas,
            weak_areas=request.weak_areas
        )
        
        # Convert to full input
        input_data = WorkRecommendationAgent.from_quick_request(quick_request)
        
        result = await agent.get_recommendations(input_data)
        
        logger.info(f"Generated {len(result.job_recommendations)} job and "
                   f"{len(result.freelance_opportunities)} freelance recommendations")
        return result
        
    except Exception as e:
        logger.error(f"Error getting work recommendations: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate recommendations: {str(e)}"
        )


@router.post(
    "/recommendations/detailed",
    response_model=WorkRecommendationResponse,
    summary="Get Detailed Work Recommendations",
    description="Get work recommendations with full profile specification"
)
async def get_detailed_work_recommendations(
    request: WorkRecommendationInput
) -> WorkRecommendationResponse:
    """Get work recommendations with full detailed input."""
    try:
        agent = WorkRecommendationAgent()
        result = await agent.get_recommendations(request)
        return result
        
    except Exception as e:
        logger.error(f"Error getting detailed work recommendations: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate recommendations: {str(e)}"
        )


# ============================================
# Specialized Endpoints
# ============================================

@router.post(
    "/jobs",
    summary="Get Job Recommendations Only",
    description="""
## Get quick job recommendations

Input your skills and career goal to get 3-5 suitable job types.
Fast and focused on what you can apply for within 1-2 months.
"""
)
async def get_jobs_only(request: QuickJobsRequest) -> dict:
    """Get quick job recommendations."""
    try:
        agent = WorkRecommendationAgent()
        
        result = await agent.get_quick_jobs(
            skills=request.skills,
            career_goal=request.career_goal,
            current_level=request.current_level
        )
        
        return {
            "career_goal": request.career_goal,
            "current_level": request.current_level,
            "skills": request.skills,
            "job_recommendations": result.get("recommendations", "")
        }
        
    except Exception as e:
        logger.error(f"Error getting job recommendations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/freelance",
    summary="Get Freelance Opportunities Only",
    description="""
## Get freelance gig recommendations

Focus on what you can start doing NOW or within 2 weeks.
Get specific gig types, earning potential, and where to find clients.
"""
)
async def get_freelance_only(request: FreelanceRequest) -> dict:
    """Get freelance-focused recommendations."""
    try:
        agent = WorkRecommendationAgent()
        
        result = await agent.get_freelance_focus(
            skills=request.skills,
            tools_known=request.tools_known,
            projects_done=request.projects_done,
            hours_per_week=request.hours_per_week,
            current_level=request.current_level
        )
        
        return {
            "skills": request.skills,
            "hours_available": request.hours_per_week,
            "freelance_opportunities": result.get("freelance_advice", "")
        }
        
    except Exception as e:
        logger.error(f"Error getting freelance recommendations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/readiness",
    summary="Check Work Readiness",
    description="Quick check of your readiness for jobs vs freelance vs practice"
)
async def check_readiness(
    skills: List[str],
    projects_done: List[str] = None,
    current_level: str = "beginner"
) -> dict:
    """Quick readiness check."""
    try:
        # Simple heuristic-based readiness check
        skill_count = len(skills)
        project_count = len(projects_done) if projects_done else 0
        
        if current_level == "advanced" and project_count >= 3:
            readiness = "junior_ready"
            advice = "You're ready to apply for junior positions"
        elif current_level in ["intermediate", "advanced"] and project_count >= 2:
            readiness = "internship_ready"
            advice = "You're ready for internships. Start applying!"
        elif skill_count >= 3 and project_count >= 1:
            readiness = "freelance_ready"
            advice = "Start with small freelance gigs to build portfolio"
        else:
            readiness = "practice_first"
            advice = "Focus on building 1-2 portfolio projects first"
        
        return {
            "readiness_level": readiness,
            "advice": advice,
            "skills_count": skill_count,
            "projects_count": project_count,
            "next_step": "Build a portfolio project" if project_count < 2 else "Start applying"
        }
        
    except Exception as e:
        logger.error(f"Error checking readiness: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# Utility Endpoints
# ============================================

@router.get(
    "/platforms",
    summary="Get Freelance Platform Types",
    description="Get information about different types of freelance platforms"
)
async def get_platform_types() -> dict:
    """Get freelance platform type information."""
    return {
        "platform_types": [
            {
                "type": "General Freelance Marketplaces",
                "description": "Broad range of projects across all fields",
                "examples_type": "Upwork-style, Fiverr-style platforms",
                "best_for": ["Beginners", "Diverse skills", "Building reviews"],
                "typical_competition": "High"
            },
            {
                "type": "Tech-Specific Platforms",
                "description": "Focused on development and tech work",
                "examples_type": "Toptal-style, developer-focused platforms",
                "best_for": ["Experienced developers", "Higher rates"],
                "typical_competition": "Medium"
            },
            {
                "type": "Project-Based Platforms",
                "description": "One-time projects and contests",
                "examples_type": "99designs-style, contest platforms",
                "best_for": ["Creative work", "Quick projects"],
                "typical_competition": "High"
            },
            {
                "type": "Direct Client Outreach",
                "description": "Finding clients through networking",
                "examples_type": "LinkedIn, personal network, cold outreach",
                "best_for": ["Higher rates", "Long-term relationships"],
                "typical_competition": "Low"
            },
            {
                "type": "Local/Student Job Boards",
                "description": "University and local opportunities",
                "examples_type": "University job boards, local business networks",
                "best_for": ["Students", "First experiences"],
                "typical_competition": "Low"
            }
        ]
    }


@router.get(
    "/job-types",
    summary="Get Entry-Level Job Types",
    description="Get common entry-level job types by field"
)
async def get_job_types(field: str = "software") -> dict:
    """Get common job types by field."""
    job_types = {
        "software": [
            "Junior Software Developer",
            "Software Engineering Intern",
            "Junior Backend Developer",
            "Junior Frontend Developer",
            "QA Tester / QA Intern"
        ],
        "data": [
            "Junior Data Analyst",
            "Data Science Intern",
            "Business Intelligence Intern",
            "Data Entry Specialist",
            "Junior Data Engineer"
        ],
        "web": [
            "Junior Web Developer",
            "Frontend Developer Intern",
            "WordPress Developer",
            "Junior Full Stack Developer",
            "Web Development Intern"
        ],
        "mobile": [
            "Junior Mobile Developer",
            "iOS/Android Intern",
            "Junior React Native Developer",
            "Mobile App Tester"
        ],
        "devops": [
            "Junior DevOps Engineer",
            "IT Support Intern",
            "Junior System Administrator",
            "Cloud Support Associate"
        ],
        "ai": [
            "AI/ML Intern",
            "Junior Machine Learning Engineer",
            "Data Annotation Specialist",
            "AI Research Assistant"
        ]
    }
    
    return {
        "field": field,
        "job_types": job_types.get(field.lower(), job_types["software"]),
        "all_fields": list(job_types.keys())
    }


@router.get(
    "/freelance-gigs",
    summary="Get Common Freelance Gig Types",
    description="Get common freelance gig types by skill area"
)
async def get_freelance_gigs(skill_area: str = "python") -> dict:
    """Get common freelance gig types by skill."""
    gigs = {
        "python": [
            {"gig": "Web Scraping", "earning": "$50-300/project"},
            {"gig": "Data Cleaning", "earning": "$30-200/project"},
            {"gig": "Automation Scripts", "earning": "$50-500/project"},
            {"gig": "API Integration", "earning": "$100-500/project"},
            {"gig": "Django/Flask Apps", "earning": "$200-1000/project"}
        ],
        "javascript": [
            {"gig": "React Components", "earning": "$50-300/project"},
            {"gig": "Landing Pages", "earning": "$100-500/project"},
            {"gig": "Bug Fixing", "earning": "$20-100/bug"},
            {"gig": "Website Updates", "earning": "$50-200/project"},
            {"gig": "Node.js API", "earning": "$150-600/project"}
        ],
        "data": [
            {"gig": "Excel/Sheets Work", "earning": "$20-100/project"},
            {"gig": "Data Visualization", "earning": "$50-300/project"},
            {"gig": "Dashboard Creation", "earning": "$100-500/project"},
            {"gig": "Data Entry", "earning": "$10-50/hour"},
            {"gig": "Survey Analysis", "earning": "$50-200/project"}
        ],
        "design": [
            {"gig": "Logo Design", "earning": "$50-200/project"},
            {"gig": "Social Media Graphics", "earning": "$20-100/set"},
            {"gig": "UI Mockups", "earning": "$100-400/project"},
            {"gig": "Presentation Design", "earning": "$50-200/project"}
        ]
    }
    
    return {
        "skill_area": skill_area,
        "gig_types": gigs.get(skill_area.lower(), gigs["python"]),
        "all_skill_areas": list(gigs.keys())
    }


# ============================================
# 🔥 Live Search Endpoints (Real APIs)
# ============================================

@router.post(
    "/search/jobs",
    response_model=LiveJobSearchResponse,
    summary="🔍 Live Job Search",
    description="""
## Search for real jobs using live APIs

### Data Sources:
- **Remotive** - Remote jobs (FREE, no API key needed)
- **Arbeitnow** - Tech jobs (FREE, no API key needed)
- **Adzuna** - Global jobs (requires API key)
- **JSearch/RapidAPI** - LinkedIn, Indeed, Glassdoor (requires API key)

### Also Returns:
Direct search URLs for: LinkedIn, Indeed, Glassdoor, Dice, Stack Overflow, Remote OK, etc.

### To enable paid APIs:
Set in your .env file:
- `ADZUNA_APP_ID` and `ADZUNA_APP_KEY`
- `RAPIDAPI_KEY` (for JSearch)
"""
)
async def search_jobs_live(request: LiveJobSearchRequest) -> LiveJobSearchResponse:
    """Search for jobs using live APIs."""
    try:
        agent = WorkRecommendationAgent()
        
        result = await agent.search_jobs_live(
            keywords=request.keywords,
            location=request.location,
            job_type=request.job_type,
            limit=request.limit
        )
        
        logger.info(f"Found {result.total_results} jobs from {len(result.providers_used)} providers")
        return result
        
    except Exception as e:
        logger.error(f"Error in live job search: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/search/jobs/quick",
    response_model=LiveJobSearchResponse,
    summary="🔍 Quick Job Search (GET)",
    description="Quick job search with query parameters"
)
async def quick_job_search(
    q: str = Query(..., description="Search query", example="Python Developer"),
    location: str = Query(default="", description="Location", example="Remote"),
    job_type: str = Query(default="", description="Job type", example="internship"),
    limit: int = Query(default=10, ge=1, le=50)
) -> LiveJobSearchResponse:
    """Quick job search with GET request."""
    try:
        agent = WorkRecommendationAgent()
        keywords = q.split()
        
        return await agent.search_jobs_live(
            keywords=keywords,
            location=location,
            job_type=job_type,
            limit=limit
        )
        
    except Exception as e:
        logger.error(f"Error in quick job search: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/search/freelance",
    response_model=FreelanceSearchResponse,
    summary="💼 Freelance Platform URLs",
    description="""
## Get search URLs for freelance platforms

Returns direct search links for:
- 🟢 **Upwork** - General freelance marketplace
- 🟢 **Fiverr** - Gig-based platform
- 🔵 **Freelancer.com** - Project bidding
- ⭐ **Toptal** - Premium developers
- 🟠 **PeoplePerHour** - UK/EU focused
- 🟣 **Guru** - Lower competition
- 💼 **FlexJobs** - Vetted remote jobs
- 🌍 **We Work Remotely** - Remote positions

Each URL is pre-filled with your skills as search terms!
"""
)
async def get_freelance_search_urls(request: FreelanceURLsRequest) -> FreelanceSearchResponse:
    """Get freelance platform search URLs."""
    try:
        agent = WorkRecommendationAgent()
        
        result = agent.get_freelance_urls(
            skills=request.skills,
            gig_types=request.gig_types if request.gig_types else None
        )
        
        logger.info(f"Generated URLs for {len(result.platforms)} platforms")
        return result
        
    except Exception as e:
        logger.error(f"Error getting freelance URLs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/search/freelance/quick",
    response_model=FreelanceSearchResponse,
    summary="💼 Quick Freelance URLs (GET)",
    description="Quick freelance platform URLs with query parameters"
)
async def quick_freelance_urls(
    skills: str = Query(..., description="Comma-separated skills", example="Python,Data Analysis,Web Scraping")
) -> FreelanceSearchResponse:
    """Quick freelance URLs with GET request."""
    try:
        agent = WorkRecommendationAgent()
        skill_list = [s.strip() for s in skills.split(",")]
        
        return agent.get_freelance_urls(skills=skill_list)
        
    except Exception as e:
        logger.error(f"Error getting quick freelance URLs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/search/full",
    response_model=FullWorkSearchResponse,
    summary="🚀 Full Work Search (AI + Live Jobs + Freelance)",
    description="""
## Complete work search with everything!

### Returns:
1. 🤖 **AI Recommendations** - Personalized job/freelance advice
2. 🔍 **Live Job Listings** - Real jobs from APIs
3. 💼 **Freelance Platform URLs** - Direct search links
4. ⚡ **Quick Links** - Easy access to all platforms

This is the most comprehensive endpoint - use it to get everything at once!
"""
)
async def full_work_search(request: FullSearchRequest) -> FullWorkSearchResponse:
    """Get complete work search with AI + live APIs + URLs."""
    try:
        agent = WorkRecommendationAgent()
        
        # Convert to QuickWorkRequest first
        quick_request = QuickWorkRequest(
            career_goal=request.career_goal,
            field_of_interest=request.field_of_interest,
            skills=request.skills,
            current_level=request.current_level,
            tools_known=request.tools_known,
            projects_done=request.projects_done,
            hours_per_week=request.hours_per_week,
            currently_learning=request.currently_learning,
            strong_areas=request.strong_areas,
            weak_areas=request.weak_areas
        )
        
        # Convert to full input
        input_data = WorkRecommendationAgent.from_quick_request(quick_request)
        
        result = await agent.get_full_recommendations(
            input_data=input_data,
            location=request.location
        )
        
        logger.info("Generated full work search response")
        return result
        
    except Exception as e:
        logger.error(f"Error in full work search: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# API Status Endpoint
# ============================================

@router.get(
    "/api-status",
    summary="Check API Configuration Status",
    description="Check which job search APIs are configured and available"
)
async def check_api_status() -> dict:
    """Check which APIs are configured."""
    agent = WorkRecommendationAgent()
    providers = agent.get_api_status()
    
    return {
        "status": "ok",
        "providers": providers,
        "free_apis": ["remotive", "arbeitnow"],
        "paid_apis": ["adzuna", "jsearch"],
        "setup_instructions": {
            "adzuna": "Get free API key at https://developer.adzuna.com/",
            "jsearch": "Get API key at https://rapidapi.com/letscrape-6bRBa3QguO5/api/jsearch"
        },
        "env_variables": {
            "adzuna": ["ADZUNA_APP_ID", "ADZUNA_APP_KEY"],
            "jsearch": ["RAPIDAPI_KEY"]
        }
    }