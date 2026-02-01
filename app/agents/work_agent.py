"""
Work Recommendation Agent

AI Career Opportunity Agent that analyzes student skills and recommends:
- Suitable Jobs (internships, junior roles, entry-level)
- Freelance Opportunities (projects, gigs, contracts)

Acts as a career coach + recruiter assistant focusing on realistic,
skill-matched opportunities.

Now enhanced with real job/freelance search capabilities!
"""

import json
import re
from typing import Optional, List, Dict, Any
from datetime import datetime
from langchain_core.messages import HumanMessage, SystemMessage

from app.providers import get_langchain_llm
from app.agents.work_prompts import (
    WORK_AGENT_SYSTEM_PROMPT,
    WORK_RECOMMENDATION_PROMPT,
    QUICK_JOB_CHECK_PROMPT,
    FREELANCE_FOCUS_PROMPT
)
from app.models.work_schemas import (
    WorkRecommendationInput,
    WorkRecommendationResponse,
    WorkReadinessAnalysis,
    JobRecommendation,
    FreelanceOpportunity,
    IncomeStrategy,
    SkillGap,
    HighImpactProject,
    QuickWorkRequest,
    SkillLevel,
    WorkReadiness,
    JobDifficulty,
    StudentWorkProfile,
    LearningState,
    LiveJobSearchResponse,
    FreelanceSearchResponse,
    FullWorkSearchResponse,
    LiveJobListing,
    JobSearchURL,
    FreelancePlatformURL
)
from app.services.work_search_client import (
    WorkSearchClient,
    JobBoardURLs,
    FreelancePlatformURLs
)


class WorkRecommendationAgent:
    """AI Career Opportunity Agent for job and freelance recommendations."""
    
    def __init__(self, provider_type: str = None):
        """Initialize the work recommendation agent."""
        self.llm = get_langchain_llm(provider_type=provider_type)
        self.search_client = WorkSearchClient()
    
    async def get_recommendations(
        self, 
        input_data: WorkRecommendationInput,
        include_live_search: bool = True
    ) -> WorkRecommendationResponse:
        """
        Get job and freelance recommendations based on student profile.
        
        Args:
            input_data: Complete student profile and learning state
            include_live_search: Whether to include live job/freelance URLs
            
        Returns:
            WorkRecommendationResponse with jobs, freelance, and strategy
        """
        # Build the prompt
        prompt = WORK_RECOMMENDATION_PROMPT.format(
            career_goal=input_data.student_profile.career_goal,
            current_level=input_data.student_profile.current_level.value,
            field_of_interest=input_data.student_profile.field_of_interest,
            skills=", ".join(input_data.student_profile.skills) or "None specified",
            tools_known=", ".join(input_data.student_profile.tools_known) or "None specified",
            projects_done=", ".join(input_data.student_profile.projects_done) or "None",
            hours_per_week=input_data.student_profile.available_hours_per_week,
            currently_learning=", ".join(input_data.learning_state.current_topics_learning) or "None",
            strong_areas=", ".join(input_data.learning_state.strong_areas) or "None specified",
            weak_areas=", ".join(input_data.learning_state.weak_areas) or "None specified"
        )
        
        messages = [
            SystemMessage(content=WORK_AGENT_SYSTEM_PROMPT),
            HumanMessage(content=prompt)
        ]
        
        response = await self.llm.ainvoke(messages)
        result = self._parse_response(response.content, input_data)
        
        # Add search URLs to recommendations
        if include_live_search:
            result = self._enrich_with_urls(result, input_data)
        
        return result
    
    def get_recommendations_sync(
        self, 
        input_data: WorkRecommendationInput
    ) -> WorkRecommendationResponse:
        """Synchronous version of get_recommendations."""
        prompt = WORK_RECOMMENDATION_PROMPT.format(
            career_goal=input_data.student_profile.career_goal,
            current_level=input_data.student_profile.current_level.value,
            field_of_interest=input_data.student_profile.field_of_interest,
            skills=", ".join(input_data.student_profile.skills) or "None specified",
            tools_known=", ".join(input_data.student_profile.tools_known) or "None specified",
            projects_done=", ".join(input_data.student_profile.projects_done) or "None",
            hours_per_week=input_data.student_profile.available_hours_per_week,
            currently_learning=", ".join(input_data.learning_state.current_topics_learning) or "None",
            strong_areas=", ".join(input_data.learning_state.strong_areas) or "None specified",
            weak_areas=", ".join(input_data.learning_state.weak_areas) or "None specified"
        )
        
        messages = [
            SystemMessage(content=WORK_AGENT_SYSTEM_PROMPT),
            HumanMessage(content=prompt)
        ]
        
        response = self.llm.invoke(messages)
        return self._parse_response(response.content, input_data)
    
    async def get_quick_jobs(
        self,
        skills: List[str],
        career_goal: str,
        current_level: str = "beginner"
    ) -> List[dict]:
        """Get quick job recommendations with minimal input."""
        prompt = QUICK_JOB_CHECK_PROMPT.format(
            skills=", ".join(skills),
            career_goal=career_goal,
            current_level=current_level
        )
        
        messages = [
            SystemMessage(content="You are a career advisor. Be practical and realistic."),
            HumanMessage(content=prompt)
        ]
        
        response = await self.llm.ainvoke(messages)
        return {"recommendations": response.content.strip()}
    
    async def get_freelance_focus(
        self,
        skills: List[str],
        tools_known: List[str],
        projects_done: List[str],
        hours_per_week: float,
        current_level: str = "beginner"
    ) -> dict:
        """Get freelance-focused recommendations."""
        prompt = FREELANCE_FOCUS_PROMPT.format(
            skills=", ".join(skills),
            tools_known=", ".join(tools_known),
            projects_done=", ".join(projects_done) if projects_done else "None",
            hours_per_week=hours_per_week,
            current_level=current_level
        )
        
        messages = [
            SystemMessage(content="You are a freelance career advisor. Be practical."),
            HumanMessage(content=prompt)
        ]
        
        response = await self.llm.ainvoke(messages)
        return {"freelance_advice": response.content.strip()}
    
    def _parse_response(
        self, 
        response_content: str, 
        input_data: WorkRecommendationInput
    ) -> WorkRecommendationResponse:
        """Parse LLM response into WorkRecommendationResponse."""
        try:
            content = response_content.strip()
            
            # Extract JSON from markdown code blocks if present
            json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', content)
            if json_match:
                content = json_match.group(1).strip()
            
            data = json.loads(content)
            
            # Parse work readiness
            readiness_data = data.get("work_readiness", {})
            work_readiness = WorkReadinessAnalysis(
                readiness_level=self._map_readiness(readiness_data.get("readiness_level", "practice_first")),
                readiness_summary=readiness_data.get("readiness_summary", ""),
                strengths_for_work=readiness_data.get("strengths_for_work", []),
                gaps_to_address=readiness_data.get("gaps_to_address", []),
                recommended_path=readiness_data.get("recommended_path", "")
            )
            
            # Parse job recommendations
            job_recommendations = []
            for job in data.get("job_recommendations", []):
                job_recommendations.append(JobRecommendation(
                    job_title=job.get("job_title", ""),
                    job_type=job.get("job_type", "internship"),
                    why_it_fits=job.get("why_it_fits", ""),
                    skills_they_have=job.get("skills_they_have", []),
                    missing_skills=job.get("missing_skills", []),
                    difficulty=self._map_difficulty(job.get("difficulty", "medium")),
                    time_to_ready=job.get("time_to_ready", "1-2 months"),
                    typical_tasks=job.get("typical_tasks", []),
                    icon=job.get("icon", "💼")
                ))
            
            # Parse freelance opportunities
            freelance_opportunities = []
            for gig in data.get("freelance_opportunities", []):
                freelance_opportunities.append(FreelanceOpportunity(
                    gig_type=gig.get("gig_type", ""),
                    example_task=gig.get("example_task", ""),
                    why_they_can_do_it=gig.get("why_they_can_do_it", ""),
                    skills_required=gig.get("skills_required", []),
                    platform_types=gig.get("platform_types", []),
                    earning_potential=gig.get("earning_potential", "$50-200"),
                    difficulty=self._map_difficulty(gig.get("difficulty", "easy_entry")),
                    icon=gig.get("icon", "💻")
                ))
            
            # Parse income strategy
            strategy_data = data.get("income_strategy", {})
            income_strategy = IncomeStrategy(
                start_freelance_now=strategy_data.get("start_freelance_now", False),
                freelance_reasoning=strategy_data.get("freelance_reasoning", ""),
                fast_income_path=strategy_data.get("fast_income_path", ""),
                long_term_career_path=strategy_data.get("long_term_career_path", ""),
                recommended_first_step=strategy_data.get("recommended_first_step", "")
            )
            
            # Parse skill gaps
            skill_gaps = []
            for gap in data.get("skill_gaps", []):
                skill_gaps.append(SkillGap(
                    skill_name=gap.get("skill_name", ""),
                    importance=gap.get("importance", ""),
                    how_to_learn=gap.get("how_to_learn", ""),
                    time_to_learn=gap.get("time_to_learn", "")
                ))
            
            # Parse high impact project
            project_data = data.get("high_impact_project", {})
            high_impact_project = HighImpactProject(
                project_name=project_data.get("project_name", "Portfolio Project"),
                description=project_data.get("description", ""),
                skills_demonstrated=project_data.get("skills_demonstrated", []),
                why_employers_care=project_data.get("why_employers_care", ""),
                estimated_time=project_data.get("estimated_time", "2-4 weeks")
            )
            
            return WorkRecommendationResponse(
                work_readiness=work_readiness,
                job_recommendations=job_recommendations,
                freelance_opportunities=freelance_opportunities,
                income_strategy=income_strategy,
                skill_gaps=skill_gaps,
                high_impact_project=high_impact_project,
                immediate_actions=data.get("immediate_actions", [])
            )
            
        except (json.JSONDecodeError, Exception) as e:
            return self._fallback_response(input_data, str(e))
    
    def _map_readiness(self, level: str) -> WorkReadiness:
        """Map string to WorkReadiness enum."""
        mapping = {
            "practice_first": WorkReadiness.PRACTICE_FIRST,
            "freelance_ready": WorkReadiness.FREELANCE_READY,
            "internship_ready": WorkReadiness.INTERNSHIP_READY,
            "junior_ready": WorkReadiness.JUNIOR_READY
        }
        return mapping.get(level.lower(), WorkReadiness.PRACTICE_FIRST)
    
    def _map_difficulty(self, difficulty: str) -> JobDifficulty:
        """Map string to JobDifficulty enum."""
        mapping = {
            "easy_entry": JobDifficulty.EASY,
            "easy": JobDifficulty.EASY,
            "medium": JobDifficulty.MEDIUM,
            "hard": JobDifficulty.HARD
        }
        return mapping.get(difficulty.lower(), JobDifficulty.MEDIUM)
    
    def _fallback_response(
        self, 
        input_data: WorkRecommendationInput, 
        error: str
    ) -> WorkRecommendationResponse:
        """Create fallback response when parsing fails."""
        profile = input_data.student_profile
        
        return WorkRecommendationResponse(
            work_readiness=WorkReadinessAnalysis(
                readiness_level=WorkReadiness.FREELANCE_READY if profile.projects_done else WorkReadiness.PRACTICE_FIRST,
                readiness_summary=f"Based on your {profile.current_level.value} level in {profile.field_of_interest}, "
                                 f"with skills in {', '.join(profile.skills[:3]) if profile.skills else 'various areas'}.",
                strengths_for_work=profile.skills[:3] if profile.skills else ["Willingness to learn"],
                gaps_to_address=["Build more projects", "Strengthen core skills"],
                recommended_path="Start with small freelance projects to build portfolio"
            ),
            job_recommendations=[
                JobRecommendation(
                    job_title=f"{profile.field_of_interest} Intern",
                    job_type="internship",
                    why_it_fits="Matches your field of interest and current level",
                    skills_they_have=profile.skills[:3] if profile.skills else [],
                    missing_skills=["Advanced skills", "Production experience"],
                    difficulty=JobDifficulty.MEDIUM,
                    time_to_ready="1-2 months",
                    typical_tasks=["Learning", "Assisting senior developers", "Small tasks"]
                )
            ],
            freelance_opportunities=[
                FreelanceOpportunity(
                    gig_type="Small Projects",
                    example_task="Help with basic tasks in your skill area",
                    why_they_can_do_it="Matches your current skill set",
                    skills_required=profile.skills[:3] if profile.skills else ["Basic programming"],
                    platform_types=["Freelance marketplaces", "Student job boards"],
                    earning_potential="$20-100/project",
                    difficulty=JobDifficulty.EASY
                )
            ],
            income_strategy=IncomeStrategy(
                start_freelance_now=len(profile.projects_done) > 0,
                freelance_reasoning="Small projects can help build portfolio while learning",
                fast_income_path="Start with small, simple tasks in your skill area",
                long_term_career_path=f"Build expertise in {profile.field_of_interest}",
                recommended_first_step="Complete one portfolio project this week"
            ),
            skill_gaps=[
                SkillGap(
                    skill_name="Portfolio Projects",
                    importance="Employers need proof of skills",
                    how_to_learn="Build projects, document them, share on GitHub",
                    time_to_learn="2-4 weeks per project"
                )
            ],
            high_impact_project=HighImpactProject(
                project_name=f"{profile.field_of_interest} Portfolio Project",
                description=f"Build a complete project showcasing your {profile.field_of_interest} skills",
                skills_demonstrated=profile.skills[:4] if profile.skills else ["Core skills"],
                why_employers_care="Demonstrates ability to complete real projects",
                estimated_time="2-4 weeks"
            ),
            immediate_actions=[
                "Identify one small project to start today",
                "Set up GitHub profile if not done",
                "Research entry-level positions in your field"
            ]
        )
    
    @staticmethod
    def from_quick_request(request: QuickWorkRequest) -> WorkRecommendationInput:
        """Convert QuickWorkRequest to WorkRecommendationInput."""
        level_map = {
            "beginner": SkillLevel.BEGINNER,
            "intermediate": SkillLevel.INTERMEDIATE,
            "advanced": SkillLevel.ADVANCED
        }
        
        return WorkRecommendationInput(
            student_profile=StudentWorkProfile(
                career_goal=request.career_goal,
                current_level=level_map.get(request.current_level.lower(), SkillLevel.BEGINNER),
                field_of_interest=request.field_of_interest,
                skills=request.skills,
                tools_known=request.tools_known,
                projects_done=request.projects_done,
                available_hours_per_week=request.hours_per_week
            ),
            learning_state=LearningState(
                current_topics_learning=request.currently_learning,
                strong_areas=request.strong_areas,
                weak_areas=request.weak_areas
            )
        )
    
    def _enrich_with_urls(
        self,
        response: WorkRecommendationResponse,
        input_data: WorkRecommendationInput
    ) -> WorkRecommendationResponse:
        """Add search URLs to job and freelance recommendations."""
        profile = input_data.student_profile
        
        # Add URLs to job recommendations
        for job in response.job_recommendations:
            job.search_urls = JobBoardURLs.get_all_search_urls(
                [job.job_title] + profile.skills[:2],
                ""  # location can be added if needed
            )
        
        # Add URLs to freelance opportunities
        for gig in response.freelance_opportunities:
            gig_keywords = [gig.gig_type] + gig.skills_required[:2]
            freelance_gigs = FreelancePlatformURLs.get_all_search_urls(gig_keywords)
            gig.platform_urls = [
                {
                    "platform": g.platform,
                    "url": g.search_url,
                    "logo": g.platform_logo,
                    "tips": g.tips
                }
                for g in freelance_gigs
            ]
        
        return response
    
    async def get_full_recommendations(
        self,
        input_data: WorkRecommendationInput,
        location: str = ""
    ) -> FullWorkSearchResponse:
        """
        Get AI recommendations + live job search + freelance platform URLs.
        
        Returns complete work search response with:
        - AI-generated recommendations
        - Live job listings from APIs
        - Freelance platform search URLs
        """
        profile = input_data.student_profile
        
        # Get AI recommendations
        ai_recommendations = await self.get_recommendations(input_data)
        
        # Search for live jobs
        job_keywords = [profile.field_of_interest] + profile.skills[:3]
        job_type = "internship" if profile.current_level == SkillLevel.BEGINNER else "junior"
        
        live_search_results = await self.search_client.search_jobs(
            keywords=job_keywords,
            location=location,
            job_type=job_type,
            limit=10
        )
        
        # Build live job response
        live_jobs = LiveJobSearchResponse(
            query=" ".join(job_keywords),
            location=location if location else None,
            live_jobs=[
                LiveJobListing(
                    title=job.title,
                    company=job.company,
                    location=job.location,
                    url=job.url,
                    salary=job.salary,
                    description=job.description,
                    source=job.source,
                    posted_date=job.posted_date,
                    job_type=job.job_type
                )
                for job in live_search_results.get("api_jobs", [])
            ],
            search_urls=[
                JobSearchURL(
                    name=url["name"],
                    url=url["url"],
                    logo=url["logo"]
                )
                for url in live_search_results.get("search_urls", [])
            ],
            providers_used=live_search_results.get("providers_used", []),
            total_results=len(live_search_results.get("api_jobs", []))
        )
        
        # Get freelance platform URLs
        freelance_results = self.search_client.get_freelance_opportunities(
            skills=profile.skills,
            gig_types=[gig.gig_type for gig in ai_recommendations.freelance_opportunities[:3]]
        )
        
        freelance_platforms = FreelanceSearchResponse(
            skills=profile.skills,
            platforms=[
                FreelancePlatformURL(
                    platform=p["platform"],
                    search_url=p["search_url"],
                    logo=p.get("logo", "🔗"),
                    tips=p.get("tips")
                )
                for p in freelance_results.get("platforms", [])
            ],
            by_skill=freelance_results.get("by_skill", {}),
            tips=freelance_results.get("tips", [])
        )
        
        # Build quick links
        quick_links = {
            "job_boards": live_search_results.get("search_urls", [])[:5],
            "freelance_platforms": [
                {"platform": p["platform"], "url": p["search_url"]}
                for p in freelance_results.get("platforms", [])[:5]
            ],
            "skill_specific": {
                skill: freelance_results.get("by_skill", {}).get(skill, [])[:3]
                for skill in profile.skills[:3]
            }
        }
        
        return FullWorkSearchResponse(
            ai_recommendations=ai_recommendations,
            live_jobs=live_jobs,
            freelance_platforms=freelance_platforms,
            quick_links=quick_links
        )
    
    async def search_jobs_live(
        self,
        keywords: List[str],
        location: str = "",
        job_type: str = "",
        limit: int = 10
    ) -> LiveJobSearchResponse:
        """
        Search for jobs using live APIs.
        
        Returns actual job listings from Adzuna, Remotive, etc.
        """
        results = await self.search_client.search_jobs(
            keywords=keywords,
            location=location,
            job_type=job_type,
            limit=limit
        )
        
        return LiveJobSearchResponse(
            query=" ".join(keywords),
            location=location if location else None,
            live_jobs=[
                LiveJobListing(
                    title=job.title,
                    company=job.company,
                    location=job.location,
                    url=job.url,
                    salary=job.salary,
                    description=job.description,
                    source=job.source,
                    posted_date=job.posted_date,
                    job_type=job.job_type
                )
                for job in results.get("api_jobs", [])
            ],
            search_urls=[
                JobSearchURL(name=url["name"], url=url["url"], logo=url["logo"])
                for url in results.get("search_urls", [])
            ],
            providers_used=results.get("providers_used", []),
            total_results=len(results.get("api_jobs", []))
        )
    
    def get_freelance_urls(
        self,
        skills: List[str],
        gig_types: List[str] = None
    ) -> FreelanceSearchResponse:
        """
        Get freelance platform search URLs for given skills.
        
        Returns URLs for Upwork, Fiverr, Freelancer, etc.
        """
        results = self.search_client.get_freelance_opportunities(
            skills=skills,
            gig_types=gig_types
        )
        
        return FreelanceSearchResponse(
            skills=skills,
            platforms=[
                FreelancePlatformURL(
                    platform=p["platform"],
                    search_url=p["search_url"],
                    logo=p.get("logo", "🔗"),
                    tips=p.get("tips")
                )
                for p in results.get("platforms", [])
            ],
            by_skill=results.get("by_skill", {}),
            tips=results.get("tips", [])
        )
    
    def get_api_status(self) -> Dict[str, bool]:
        """Check which job search APIs are configured."""
        return self.search_client.get_available_providers()
