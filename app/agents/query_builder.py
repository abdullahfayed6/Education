from __future__ import annotations

from app.models.schemas import QuerySpec, UserProfile


TRACK_TITLES = {
    "data_scientist": ["Data Science Intern", "Machine Learning Intern"],
    "ai_engineer": ["AI Intern", "Machine Learning Intern"],
    "data_engineer": ["Data Engineering Intern", "ETL Intern"],
    "backend": ["Backend Intern", "Software Engineer Intern"],
    "cybersecurity": ["Cybersecurity Intern", "Security Analyst Intern"],
}


class QueryBuilderAgent:
    def build(self, profile: UserProfile) -> list[QuerySpec]:
        titles = TRACK_TITLES.get(profile.track, ["Intern", "Junior Intern"])
        skills = profile.skills.hard + profile.skills.tools
        skill_clause = " OR ".join(sorted(set(skills))) if skills else "Python"
        location = "Remote" if profile.location_preference in {"remote", "hybrid"} else "Cairo"
        title_clause = " OR ".join(titles)
        boolean_query = f"({title_clause}) AND ({skill_clause}) AND ({location})"
        linkedin_query = f"site:linkedin.com/jobs {title_clause} {location} {skill_clause}"
        general_query = f"{title_clause} internship {location} {skill_clause}"
        return [
            QuerySpec(query=boolean_query, provider="boolean", rationale="Boolean query for job boards."),
            QuerySpec(query=linkedin_query, provider="search", rationale="Search engine query for LinkedIn listings."),
            QuerySpec(query=general_query, provider="search", rationale="Broad search query for job sources."),
        ]
