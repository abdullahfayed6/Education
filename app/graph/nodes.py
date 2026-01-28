"""LangGraph node functions for the matching workflow."""
from __future__ import annotations

import logging
from datetime import datetime
from uuid import uuid4

from langchain_core.runnables import RunnableConfig

from app.config import settings
from app.graph.state import MatchState
from app.models.schemas import (
    MatchResultRun,
    OpportunityClean,
    OpportunityScore,
    QuerySpec,
    SkillBuckets,
    UserProfile,
)
from app.services.search_client import get_search_client, EGYPTIAN_COMPANIES
from app.services.linkedin_client import get_linkedin_client, TRACK_TITLES as LINKEDIN_TRACK_TITLES
from app.services.openai_client import get_openai_client

logger = logging.getLogger("matcher")

# ============ Constants ============
YEAR_MAP = {1: "freshman", 2: "sophomore", 3: "junior", 4: "senior", 5: "graduate"}
SOFT_SKILLS = {"communication", "teamwork", "leadership", "collaboration", "problem solving", "presentation", "negotiation"}
TOOLS = {"python", "sql", "pandas", "tensorflow", "pytorch", "docker", "aws", "git", "excel", "kubernetes", "azure", "gcp", 
         "java", "javascript", "typescript", "react", "node.js", "django", "flask", "fastapi", "mongodb", "postgresql",
         "mysql", "redis", "kafka", "spark", "hadoop", "tableau", "power bi", "figma", "jira", "confluence"}

# Enhanced track titles mapping
TRACK_TITLES = {
    "computer science": ["Software Engineer Intern", "Software Developer Intern", "SWE Intern", "Developer Intern"],
    "data science": ["Data Science Intern", "Data Scientist Intern", "Data Analyst Intern", "Analytics Intern"],
    "data scientist": ["Data Science Intern", "Data Scientist Intern", "ML Intern", "Analytics Intern"],
    "ai engineer": ["AI Intern", "Machine Learning Intern", "ML Engineer Intern", "AI/ML Intern"],
    "machine learning": ["Machine Learning Intern", "ML Engineer Intern", "AI Intern", "Deep Learning Intern"],
    "data engineer": ["Data Engineering Intern", "Data Engineer Intern", "ETL Intern", "Big Data Intern"],
    "data engineering": ["Data Engineering Intern", "Data Engineer Intern", "ETL Intern", "Big Data Intern"],
    "backend": ["Backend Intern", "Backend Developer Intern", "Software Engineer Intern", "API Developer Intern"],
    "backend developer": ["Backend Intern", "Backend Developer Intern", "Server-Side Developer Intern"],
    "frontend": ["Frontend Intern", "Frontend Developer Intern", "UI Developer Intern", "React Intern"],
    "frontend developer": ["Frontend Intern", "Frontend Developer Intern", "Web Developer Intern"],
    "full stack": ["Full Stack Intern", "Full Stack Developer Intern", "Web Developer Intern"],
    "software engineering": ["Software Engineer Intern", "Software Developer Intern", "SDE Intern", "Developer Intern"],
    "cybersecurity": ["Cybersecurity Intern", "Security Analyst Intern", "InfoSec Intern", "Security Engineer Intern"],
    "devops": ["DevOps Intern", "DevOps Engineer Intern", "SRE Intern", "Platform Engineer Intern"],
    "cloud": ["Cloud Intern", "Cloud Engineer Intern", "AWS Intern", "Azure Intern"],
    "mobile": ["Mobile Developer Intern", "iOS Intern", "Android Intern", "Mobile Engineer Intern"],
    "product": ["Product Intern", "Product Manager Intern", "APM Intern", "Product Management Intern"],
    "business": ["Business Analyst Intern", "Business Intelligence Intern", "BI Intern", "Strategy Intern"],
    "qa": ["QA Intern", "Quality Assurance Intern", "Test Engineer Intern", "SDET Intern"],
    "ui/ux": ["UI/UX Intern", "UX Designer Intern", "Product Designer Intern", "Design Intern"],
}

# Platform-specific search strategies
PLATFORM_SEARCH_STRATEGIES = {
    "linkedin": {
        "egypt": ["software intern Egypt", "internship Cairo", "تدريب مصر"],
        "remote": ["remote internship worldwide", "work from home intern"],
        "abroad": ["internship visa sponsorship", "international intern program"],
    },
    "wuzzuf": {
        "egypt": ["internship", "تدريب", "fresh graduate", "junior"],
    },
    "indeed": {
        "egypt": ["internship Egypt", "intern Cairo", "graduate program Egypt"],
        "remote": ["remote internship", "virtual internship"],
        "abroad": ["internship USA", "internship Europe", "internship UAE"],
    },
}

# Scoring weights (enhanced)
RUBRIC = {
    "track_alignment": 25,
    "skills_match": 30,
    "academic_fit": 10,
    "preference_fit": 15,
    "readiness": 10,
    "platform_quality": 5,
    "company_reputation": 5,
}

# Platform quality scores
PLATFORM_SCORES = {
    "LinkedIn": 5,
    "Wuzzuf": 5,
    "Indeed": 4,
    "Glassdoor": 4,
    "Forasna": 4,
    "Bayt": 3,
    "Tanqeeb": 3,
    "Google Jobs": 2,
    "mock": 1,
}


# ============ Node Functions ============

def normalize_profile(state: MatchState, config: RunnableConfig) -> dict:
    """Normalize user input into a structured profile."""
    user_input = state["user_input"]
    
    year_level = YEAR_MAP.get(user_input.academic_year, "unknown")
    normalized_skills = [skill.strip().lower() for skill in user_input.skills if skill.strip()]
    
    hard, tools, soft = [], [], []
    for skill in normalized_skills:
        if skill in SOFT_SKILLS:
            soft.append(skill)
        elif skill in TOOLS:
            tools.append(skill)
        else:
            hard.append(skill)
    
    buckets = SkillBuckets(
        hard=sorted(set(hard)), 
        tools=sorted(set(tools)), 
        soft=sorted(set(soft))
    )
    
    profile = UserProfile(
        year_level=year_level,
        track=user_input.track.strip().lower(),
        location_preference=user_input.preference,
        skills=buckets,
        seniority_target="intern",
    )
    
    logger.info("Profile normalized", extra={"profile": profile.model_dump()})
    return {"profile": profile}


# ============ LinkedIn Boolean Query Builder ============

# Location groups for boolean queries
EGYPT_LOCATIONS = ["Egypt", "Cairo", "Giza", "Alexandria", "Smart Village", "New Cairo", "6th of October"]
REMOTE_KEYWORDS = ["Remote", "Work from Home", "Worldwide", "Anywhere"]
ABROAD_LOCATIONS = ["USA", "United States", "UK", "Germany", "UAE", "Dubai", "Canada", "Europe"]


def _build_titles_clause(titles: list[str]) -> str:
    """Build OR clause for job titles: ("Title1" OR "Title2")"""
    return "(" + " OR ".join([f'"{t}"' for t in titles[:4]]) + ")"


def _build_location_clause(location_preference: str) -> str:
    """Build OR clause for locations based on preference."""
    if location_preference == "egypt":
        locs = EGYPT_LOCATIONS[:5]
        return "(" + " OR ".join(locs) + ")"
    elif location_preference == "remote":
        return '(Remote OR "Work from Home" OR Worldwide)'
    elif location_preference == "abroad":
        locs = ABROAD_LOCATIONS[:5]
        return "(" + " OR ".join(locs) + ")"
    else:
        return "(Egypt OR Cairo OR Remote)"


def _build_skills_clause(skills: list[str]) -> str:
    """Build OR clause for skills if enough skills provided."""
    if skills and len(skills) >= 2:
        top_skills = [s for s in skills[:4] if len(s) > 2]  # Filter short strings
        if top_skills:
            return " ".join(top_skills)  # Simple space-separated for Google Jobs
    return ""


def build_queries(state: MatchState, config: RunnableConfig) -> dict:
    """
    Build a simple search query for Google Jobs API.
    
    OPTIMIZED for API credits: Uses only 1 query = 1 API credit.
    Google Jobs works better with simple keyword queries.
    """
    profile = state["profile"]
    
    # Get job titles for the track
    track_key = profile.track.lower().strip()
    titles = LINKEDIN_TRACK_TITLES.get(track_key, LINKEDIN_TRACK_TITLES.get("software engineering", ["Software Intern"]))
    
    # Use first title (most relevant)
    primary_title = titles[0] if titles else "Software Intern"
    
    # Get top skills
    skills = profile.skills.hard + profile.skills.tools
    skills_str = " ".join(skills[:3]) if skills else ""
    
    # Build simple query: "Data Science Intern python sql"
    if skills_str:
        query = f"{primary_title} {skills_str}"
    else:
        query = primary_title
    
    queries = [
        QuerySpec(
            query=query,
            provider="linkedin",
            rationale=f"LinkedIn search for {profile.track} internships via SerpAPI (1 API credit)"
        )
    ]
    
    logger.info("Query built (1 API credit)", extra={
        "query": query,
        "preference": profile.location_preference
    })
    return {"queries": queries}


def retrieve_opportunities(state: MatchState, config: RunnableConfig) -> dict:
    """
    Retrieve opportunities from LinkedIn using ONE boolean query.
    
    OPTIMIZED: Uses only 1 API credit per search.
    """
    queries = state["queries"]
    profile = state["profile"]
    client = get_linkedin_client()
    
    all_results = []
    seen_urls = set()
    seen_titles = set()
    required_count = settings.max_results  # Now 10
    
    # Use ONLY the first query (1 API credit)
    if queries:
        query = queries[0]
        try:
            logger.info(f"Searching LinkedIn: {query.query[:80]}...")
            results = client.search(query.query, required_count, profile.location_preference)
            
            for r in results:
                title_key = r.title.lower()[:50]
                if r.url not in seen_urls and title_key not in seen_titles:
                    seen_urls.add(r.url)
                    seen_titles.add(title_key)
                    all_results.append(r)
                    
        except Exception as e:
            logger.warning(f"LinkedIn query failed: {e}")
    
    final_results = all_results[:required_count]
    
    logger.info(f"Retrieved {len(final_results)} LinkedIn opportunities (1 API credit used)")
    
    return {"raw_opportunities": final_results}


def clean_opportunities(state: MatchState, config: RunnableConfig) -> dict:
    """Clean and deduplicate opportunities."""
    raw_opportunities = state["raw_opportunities"]
    
    seen = set()
    cleaned = []
    
    for item in raw_opportunities:
        key = (item.title.lower(), item.company.lower())
        if key in seen:
            continue
        seen.add(key)
        
        # Infer work type from location
        location_lower = item.location.lower()
        if "remote" in location_lower:
            work_type = "Remote"
        elif "hybrid" in location_lower:
            work_type = "Hybrid"
        elif item.location:
            work_type = "On-site"
        else:
            work_type = None
        
        cleaned.append(OpportunityClean(
            title=item.title.strip(),
            company=item.company.strip(),
            location=item.location.strip() or "Unknown",
            url=item.url,
            source=item.source,
            description=item.snippet or "",
            work_type=work_type,
            posted_date=item.posted_date,
        ))
    
    logger.info("Cleaned opportunities", extra={"count": len(cleaned)})
    return {"clean_opportunities": cleaned}


def score_opportunities(state: MatchState, config: RunnableConfig) -> dict:
    """Score opportunities with enhanced multi-criteria algorithm."""
    profile = state["profile"]
    opportunities = state["clean_opportunities"]
    
    # Location indicators for matching
    egypt_indicators = {
        "egypt", "cairo", "alexandria", "giza", "maadi", "nasr city", "6th october", 
        "new cairo", "smart village", "heliopolis", "dokki", "zamalek", "mohandessin",
        "مصر", "القاهرة", "الإسكندرية", "الجيزة"
    }
    
    international_indicators = {
        "usa", "united states", "uk", "germany", "france", "canada", "australia",
        "uae", "dubai", "saudi", "qatar", "kuwait", "netherlands", "sweden"
    }
    
    scored = []
    for opp in opportunities:
        text = f"{opp.title} {opp.description} {opp.company}".lower()
        location_lower = opp.location.lower()
        company_lower = opp.company.lower()
        
        score = 0
        reasons = []
        
        # ============ TRACK ALIGNMENT (25 points) ============
        track_key = profile.track.lower().strip()
        track_titles = TRACK_TITLES.get(track_key, [profile.track])
        
        track_match = False
        for title_variant in track_titles:
            if title_variant.lower() in text:
                track_match = True
                break
        
        # Also check track keywords
        track_words = track_key.replace("_", " ").replace("-", " ").split()
        if track_match or any(word in text for word in track_words if len(word) > 2):
            score += RUBRIC["track_alignment"]
            reasons.append("✅ Role aligns with your track.")
        elif "intern" in text and any(word in text for word in ["software", "developer", "engineer", "data", "analyst"]):
            score += int(RUBRIC["track_alignment"] * 0.5)
            reasons.append("Role is in a related tech field.")
        
        # ============ SKILLS MATCH (30 points) ============
        user_skills = set(profile.skills.hard + profile.skills.tools)
        matched_skills = []
        
        for skill in user_skills:
            # More flexible matching (handle variations)
            skill_lower = skill.lower()
            if skill_lower in text:
                matched_skills.append(skill)
            elif skill_lower == "python" and ("py" in text or "django" in text or "flask" in text):
                matched_skills.append(skill)
            elif skill_lower == "javascript" and ("js" in text or "react" in text or "node" in text or "typescript" in text):
                matched_skills.append(skill)
            elif skill_lower == "sql" and ("database" in text or "mysql" in text or "postgresql" in text):
                matched_skills.append(skill)
        
        if user_skills:
            skill_ratio = len(matched_skills) / len(user_skills)
            skill_score = int(skill_ratio * RUBRIC["skills_match"])
            score += skill_score
            if matched_skills:
                reasons.append(f"🛠️ Matched skills: {', '.join(sorted(matched_skills)[:5])}.")
        else:
            score += int(RUBRIC["skills_match"] * 0.3)  # Partial score if no skills specified
        
        # ============ ACADEMIC FIT (10 points) ============
        if profile.year_level in {"junior", "senior", "graduate"}:
            score += RUBRIC["academic_fit"]
            reasons.append("🎓 Your academic level is a great fit.")
        elif profile.year_level == "sophomore":
            score += int(RUBRIC["academic_fit"] * 0.7)
            reasons.append("Your academic level is acceptable.")
        else:
            score += int(RUBRIC["academic_fit"] * 0.5)
        
        # ============ LOCATION/PREFERENCE FIT (15 points) ============
        location_score = 0
        
        if profile.location_preference == "egypt":
            if any(indicator in location_lower for indicator in egypt_indicators):
                location_score = RUBRIC["preference_fit"]
                reasons.append("📍 Located in Egypt as preferred!")
            elif "remote" in location_lower or opp.work_type == "Remote":
                location_score = int(RUBRIC["preference_fit"] * 0.7)
                reasons.append("🏠 Remote position (can work from Egypt).")
            elif any(indicator in location_lower for indicator in international_indicators):
                location_score = -5  # Penalty for international when Egypt preferred
                reasons.append("⚠️ Location is outside Egypt.")
            else:
                location_score = int(RUBRIC["preference_fit"] * 0.3)
                
        elif profile.location_preference == "remote":
            if opp.work_type == "Remote" or "remote" in location_lower:
                location_score = RUBRIC["preference_fit"]
                reasons.append("🏠 Remote position as preferred!")
            elif opp.work_type == "Hybrid":
                location_score = int(RUBRIC["preference_fit"] * 0.6)
                reasons.append("Hybrid position available.")
            else:
                location_score = int(RUBRIC["preference_fit"] * 0.2)
                
        elif profile.location_preference == "abroad":
            if any(indicator in location_lower for indicator in international_indicators):
                location_score = RUBRIC["preference_fit"]
                reasons.append("🌍 International opportunity!")
            elif not any(indicator in location_lower for indicator in egypt_indicators):
                location_score = int(RUBRIC["preference_fit"] * 0.5)
                reasons.append("Potential international position.")
            else:
                location_score = 0
                reasons.append("Located in Egypt (you prefer abroad).")
        else:
            # Hybrid preference
            location_score = int(RUBRIC["preference_fit"] * 0.5)
        
        score += location_score
        
        # ============ READINESS/LEVEL (10 points) ============
        title_lower = opp.title.lower()
        if "intern" in title_lower:
            score += RUBRIC["readiness"]
            reasons.append("Entry-level internship role.")
        elif "junior" in title_lower or "entry" in title_lower or "graduate" in title_lower:
            score += int(RUBRIC["readiness"] * 0.8)
            reasons.append("Entry-level position.")
        elif "senior" in title_lower or "lead" in title_lower or "manager" in title_lower:
            score += 0  # Not suitable for interns
            reasons.append("⚠️ May require more experience.")
        else:
            score += int(RUBRIC["readiness"] * 0.5)
        
        # ============ PLATFORM QUALITY (5 points) ============
        platform_score = PLATFORM_SCORES.get(opp.source, 2)
        score += platform_score
        if platform_score >= 4:
            reasons.append(f"📱 Found on {opp.source}.")
        
        # ============ COMPANY REPUTATION (5 points) ============
        # Check if company is a known Egyptian tech company
        company_boost = 0
        for known_company in EGYPTIAN_COMPANIES:
            if known_company.lower() in company_lower or company_lower in known_company.lower():
                company_boost = RUBRIC["company_reputation"]
                reasons.append(f"🏢 {opp.company} is a recognized tech company!")
                break
        
        # Also boost for well-known international companies
        if company_boost == 0:
            big_tech = ["google", "microsoft", "amazon", "meta", "apple", "netflix", "uber", "airbnb"]
            if any(tech in company_lower for tech in big_tech):
                company_boost = RUBRIC["company_reputation"]
                reasons.append(f"🌟 {opp.company} is a top tech company!")
        
        score += company_boost
        
        # ============ ENSURE VALID SCORE ============
        score = max(0, min(100, score))  # Clamp between 0-100
        
        scored.append({
            "opp": opp,
            "score": score,
            "fallback_reasons": reasons,
        })
    
    # ============ USE AI TO GENERATE PERSONALIZED REASONS ============
    ai_client = get_openai_client()
    user_skills = profile.skills.hard + profile.skills.tools
    
    final_scored = []
    for item in scored:
        opp = item["opp"]
        score = item["score"]
        
        if ai_client:
            try:
                ai_reasons = ai_client.generate_match_reasons(
                    job_title=opp.title,
                    company=opp.company,
                    job_description=opp.description or "",
                    user_track=profile.track,
                    user_skills=user_skills,
                    user_year=profile.year_level,
                    location_preference=profile.location_preference,
                    job_location=opp.location,
                    score=score,
                )
                reasons = ai_reasons
            except Exception as e:
                logger.warning(f"AI reasons failed: {e}")
                reasons = item["fallback_reasons"]
        else:
            reasons = item["fallback_reasons"]
        
        final_scored.append(OpportunityScore(
            title=opp.title,
            company=opp.company,
            location=opp.location,
            url=opp.url,
            source=opp.source,
            work_type=opp.work_type,
            score=score,
            reasons=reasons,
        ))
    
    logger.info("Scored opportunities with AI reasons", extra={"count": len(final_scored)})
    return {"scored_opportunities": final_scored}


def rank_opportunities(state: MatchState, config: RunnableConfig) -> dict:
    """Rank and select top opportunities with diversity."""
    scored = state["scored_opportunities"]
    
    sorted_items = sorted(scored, key=lambda x: x.score, reverse=True)
    
    top = []
    company_counts: dict[str, int] = {}
    
    for item in sorted_items:
        company_key = item.company.lower()
        count = company_counts.get(company_key, 0)
        
        # Limit 2 per company for diversity
        if count >= 2:
            continue
        
        top.append(item)
        company_counts[company_key] = count + 1
        
        if len(top) >= settings.top_k:
            break
    
    logger.info("Ranked opportunities", extra={"count": len(top)})
    return {"ranked_opportunities": top}


def build_result(state: MatchState, config: RunnableConfig) -> dict:
    """Build the final result object."""
    result = MatchResultRun(
        run_id=uuid4(),
        created_at=datetime.utcnow(),
        normalized_profile=state["profile"],
        generated_queries=state["queries"],
        opportunities_top20=state["clean_opportunities"],
        ranked_top5=state["ranked_opportunities"],
    )
    
    logger.info("Result built", extra={"run_id": str(result.run_id)})
    return {"result": result}
