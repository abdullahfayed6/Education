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
from app.services.search_client import get_search_client

logger = logging.getLogger("matcher")

# ============ Constants ============
YEAR_MAP = {1: "freshman", 2: "sophomore", 3: "junior", 4: "senior", 5: "graduate"}
SOFT_SKILLS = {"communication", "teamwork", "leadership", "collaboration", "problem solving"}
TOOLS = {"python", "sql", "pandas", "tensorflow", "pytorch", "docker", "aws", "git", "excel"}

TRACK_TITLES = {
    "computer science": ["Software Engineer Intern", "Data Science Intern", "ML Intern"],
    "data science": ["Data Science Intern", "Machine Learning Intern", "Data Analyst Intern"],
    "ai engineer": ["AI Intern", "Machine Learning Intern"],
    "data engineer": ["Data Engineering Intern", "ETL Intern"],
    "backend": ["Backend Intern", "Software Engineer Intern"],
    "software engineering": ["Software Engineer Intern", "Full Stack Intern", "Backend Intern"],
    "cybersecurity": ["Cybersecurity Intern", "Security Analyst Intern"],
    "business": ["Business Analyst Intern", "Product Intern"],
}

RUBRIC = {
    "track_alignment": 30,
    "skills_match": 35,
    "academic_fit": 15,
    "preference_fit": 10,
    "readiness": 10,
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


def build_queries(state: MatchState, config: RunnableConfig) -> dict:
    """Build search queries based on user profile with location-specific targeting."""
    profile = state["profile"]
    
    titles = TRACK_TITLES.get(profile.track, ["Intern", "Internship"])
    skills = profile.skills.hard + profile.skills.tools
    skill_clause = " ".join(sorted(set(skills))[:3]) if skills else ""
    
    queries = []
    
    if profile.location_preference == "egypt":
        # Egypt-specific queries - target Egyptian companies and locations
        egypt_locations = ["Cairo", "Alexandria", "Giza", "Egypt"]
        egypt_companies = ["Vodafone Egypt", "Orange Egypt", "Valeo", "Dell Egypt", "IBM Egypt", "Microsoft Egypt"]
        
        for title in titles[:2]:
            # Query 1: Direct Egypt search
            queries.append(QuerySpec(
                query=f"{title} internship Egypt Cairo {skill_clause}",
                provider="search",
                rationale=f"Search for {title} in Egypt"
            ))
            
            # Query 2: Arabic-friendly search
            queries.append(QuerySpec(
                query=f"تدريب {title} مصر {skill_clause}",
                provider="search",
                rationale=f"Arabic search for {title} internship"
            ))
        
        # Query 3: Egyptian job boards style
        queries.append(QuerySpec(
            query=f"internship {profile.track} Cairo Egypt 2024 2025 {skill_clause}",
            provider="search",
            rationale="General Egypt internship search"
        ))
        
        # Query 4: Major Egyptian tech companies
        queries.append(QuerySpec(
            query=f"software intern Egypt Vodafone Orange Valeo IBM {skill_clause}",
            provider="search",
            rationale="Major Egyptian tech companies"
        ))
        
    elif profile.location_preference == "remote":
        for title in titles[:2]:
            queries.append(QuerySpec(
                query=f"{title} internship remote worldwide {skill_clause}",
                provider="search",
                rationale=f"Remote {title} search"
            ))
        queries.append(QuerySpec(
            query=f"remote internship {profile.track} work from home {skill_clause}",
            provider="search",
            rationale="Remote work internship"
        ))
        
    elif profile.location_preference == "abroad":
        # International opportunities (US, Europe, Gulf)
        for title in titles[:2]:
            queries.append(QuerySpec(
                query=f"{title} internship international visa sponsorship {skill_clause}",
                provider="search",
                rationale=f"International {title} with visa"
            ))
        queries.append(QuerySpec(
            query=f"internship {profile.track} USA Europe UAE {skill_clause}",
            provider="search",
            rationale="International markets search"
        ))
        
    else:
        # Default/hybrid
        for title in titles[:2]:
            queries.append(QuerySpec(
                query=f"{title} internship {skill_clause}",
                provider="search",
                rationale=f"General {title} search"
            ))
    
    logger.info("Queries built", extra={"count": len(queries)})
    return {"queries": queries}


def retrieve_opportunities(state: MatchState, config: RunnableConfig) -> dict:
    """Retrieve exactly MAX_RESULTS opportunities from search provider."""
    queries = state["queries"]
    profile = state["profile"]
    client = get_search_client()
    
    all_results = []
    seen_urls = set()
    required_count = settings.max_results
    
    # First pass: search with all queries
    for query in queries:
        if len(all_results) >= required_count:
            break
        results = client.search(query.query, required_count)
        for r in results:
            if r.url not in seen_urls:
                seen_urls.add(r.url)
                all_results.append(r)
    
    # If we don't have enough results, try additional queries based on location preference
    if len(all_results) < required_count:
        if profile.location_preference == "egypt":
            fallback_queries = [
                f"internship Cairo Egypt {profile.track}",
                f"تدريب صيفي مصر برمجة",
                f"junior developer Egypt Cairo",
                f"software internship Egypt 2024 2025",
                f"Vodafone Egypt internship",
                f"Orange Egypt graduate program",
                f"tech internship Egypt",
            ]
        elif profile.location_preference == "remote":
            fallback_queries = [
                f"remote internship {profile.track} worldwide",
                f"work from home internship software",
                f"remote junior developer position",
                f"virtual internship tech",
            ]
        elif profile.location_preference == "abroad":
            fallback_queries = [
                f"internship {profile.track} USA visa sponsorship",
                f"internship Europe software",
                f"internship UAE Dubai tech",
                f"international internship program",
            ]
        else:
            fallback_queries = [
                f"{profile.track} internship 2024",
                f"software engineer intern",
                f"data science internship",
            ]
        
        for fallback_query in fallback_queries:
            if len(all_results) >= required_count:
                break
            results = client.search(fallback_query, required_count - len(all_results))
            for r in results:
                if r.url not in seen_urls:
                    seen_urls.add(r.url)
                    all_results.append(r)
    
    # Ensure we return exactly the required count (or all if less available)
    final_results = all_results[:required_count]
    
    logger.info("Retrieved opportunities", extra={"count": len(final_results), "required": required_count})
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
    """Score each opportunity against the user profile."""
    profile = state["profile"]
    opportunities = state["clean_opportunities"]
    
    # Egyptian cities and indicators for location matching
    egypt_indicators = {"egypt", "cairo", "alexandria", "giza", "maadi", "nasr city", "6th october", "new cairo", "مصر", "القاهرة"}
    
    scored = []
    for opp in opportunities:
        text = f"{opp.title} {opp.description}".lower()
        location_lower = opp.location.lower()
        score = 0
        reasons = []
        missing = []
        
        # Track alignment (30 points)
        track_words = profile.track.replace("_", " ").split()
        if any(word in text for word in track_words) or profile.track in text:
            score += RUBRIC["track_alignment"]
            reasons.append("Role aligns with your track.")
        
        # Skills match (35 points)
        user_skills = set(profile.skills.hard + profile.skills.tools)
        matched_skills = [skill for skill in user_skills if skill in text]
        skill_score = int((len(matched_skills) / max(len(user_skills), 1)) * RUBRIC["skills_match"])
        score += skill_score
        if matched_skills:
            reasons.append(f"Matched skills: {', '.join(sorted(matched_skills))}.")
        
        # Academic fit (15 points)
        if profile.year_level in {"junior", "senior", "graduate"}:
            score += RUBRIC["academic_fit"]
            reasons.append("Your academic level is a good fit.")
        else:
            score += int(RUBRIC["academic_fit"] * 0.6)
        
        # Location/Preference fit (10 points) - Enhanced for Egypt
        location_matched = False
        if profile.location_preference == "egypt":
            # Check if location contains any Egypt indicator
            if any(indicator in location_lower for indicator in egypt_indicators):
                score += RUBRIC["preference_fit"]
                reasons.append("📍 Location in Egypt as preferred!")
                location_matched = True
            elif "anywhere" in location_lower or "remote" in location_lower:
                # Remote jobs are acceptable for Egypt preference too
                score += int(RUBRIC["preference_fit"] * 0.5)
                reasons.append("Remote position (can work from Egypt).")
                location_matched = True
            # Penalize jobs clearly in other countries
            elif any(loc in location_lower for loc in ["usa", "united states", ", md", ", dc", ", ca", ", ny", ", tx"]):
                score -= 10  # Penalty for clearly US-based jobs
                reasons.append("⚠️ Location is outside Egypt.")
        elif profile.location_preference in {"remote", "hybrid"} and opp.work_type in {"Remote", "Hybrid"}:
            score += RUBRIC["preference_fit"]
            reasons.append("Work type matches your preference.")
            location_matched = True
        elif profile.location_preference == "abroad" and not any(indicator in location_lower for indicator in egypt_indicators):
            score += RUBRIC["preference_fit"]
            reasons.append("International opportunity.")
            location_matched = True
        
        # Readiness (10 points)
        if "intern" in opp.title.lower():
            score += RUBRIC["readiness"]
            reasons.append("Entry-level internship role.")
        else:
            score += int(RUBRIC["readiness"] * 0.5)
        
        # Ensure score is not negative
        score = max(0, score)
        
        # Missing skills
        missing = [s for s in user_skills if s not in matched_skills][:3]
        recommended = [f"Build a project using {s}." for s in missing] if missing else ["Keep developing your portfolio."]
        
        scored.append(OpportunityScore(
            title=opp.title,
            company=opp.company,
            location=opp.location,
            url=opp.url,
            source=opp.source,
            work_type=opp.work_type,
            score=score,
            reasons=reasons if reasons else ["General internship opportunity."],
            missing_skills=missing,
            recommended_actions=recommended,
        ))
    
    logger.info("Scored opportunities", extra={"count": len(scored)})
    return {"scored_opportunities": scored}


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


def build_coach_plan(state: MatchState, config: RunnableConfig) -> dict:
    """Generate a coaching plan based on matched opportunities."""
    profile = state["profile"]
    opportunities = state["ranked_opportunities"]
    
    # Collect missing skills
    missing = []
    for opp in opportunities:
        missing.extend(opp.missing_skills)
    unique_missing = list(dict.fromkeys(missing))[:5]
    
    two_weeks = [
        "Review top matched internships and tailor your resume.",
        "Update your LinkedIn profile with relevant skills.",
    ]
    
    one_month = [f"Complete a project using {skill}." for skill in unique_missing] if unique_missing else [
        "Build a portfolio project aligned with your track."
    ]
    
    coach_plan = {
        "next_2_weeks": two_weeks,
        "next_1_month": one_month,
        "notes": [f"Focus track: {profile.track.title()}"]
    }
    
    logger.info("Coach plan generated")
    return {"coach_plan": coach_plan}


def build_result(state: MatchState, config: RunnableConfig) -> dict:
    """Build the final result object."""
    result = MatchResultRun(
        run_id=uuid4(),
        created_at=datetime.utcnow(),
        normalized_profile=state["profile"],
        generated_queries=state["queries"],
        opportunities_top20=state["clean_opportunities"],
        ranked_top5=state["ranked_opportunities"],
        coach_plan=state["coach_plan"],
    )
    
    logger.info("Result built", extra={"run_id": str(result.run_id)})
    return {"result": result}
