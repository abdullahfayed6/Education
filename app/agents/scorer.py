from __future__ import annotations

from app.models.schemas import OpportunityClean, OpportunityScore, UserProfile
from app.services.openai_client import OpenAIClient


RUBRIC = {
    "track_alignment": 30,
    "skills_match": 35,
    "academic_fit": 15,
    "preference_fit": 10,
    "readiness": 10,
}


class ScoringAgent:
    def __init__(self) -> None:
        self.client = OpenAIClient()

    def score(self, profile: UserProfile, opportunity: OpportunityClean) -> OpportunityScore:
        llm_score = self.client.score_opportunity(profile, opportunity, RUBRIC)
        if llm_score:
            return llm_score
        return self._rule_score(profile, opportunity)

    def _rule_score(self, profile: UserProfile, opportunity: OpportunityClean) -> OpportunityScore:
        text = f"{opportunity.title} {opportunity.description}".lower()
        score = 0
        reasons = []
        missing = []

        track_hit = 0
        if profile.track.replace("_", " ") in text:
            track_hit = RUBRIC["track_alignment"]
            reasons.append("Role aligns with selected track.")
        score += track_hit

        user_skills = set(profile.skills.hard + profile.skills.tools)
        matched_skills = [skill for skill in user_skills if skill in text]
        skill_score = int((len(matched_skills) / max(len(user_skills), 1)) * RUBRIC["skills_match"])
        if matched_skills:
            reasons.append(f"Matched skills: {', '.join(sorted(matched_skills))}.")
        score += skill_score

        if profile.year_level in {"junior", "senior"}:
            score += RUBRIC["academic_fit"]
            reasons.append("Academic year fits typical internship requirements.")
        else:
            score += int(RUBRIC["academic_fit"] * 0.6)
            reasons.append("Academic year slightly below typical requirements.")

        preference_score = 0
        if profile.location_preference in {"remote", "hybrid"} and opportunity.work_type in {"Remote", "Hybrid"}:
            preference_score = RUBRIC["preference_fit"]
            reasons.append("Work type matches preference.")
        elif profile.location_preference == "egypt" and "egypt" in opportunity.location.lower():
            preference_score = RUBRIC["preference_fit"]
            reasons.append("Location matches Egypt preference.")
        elif profile.location_preference == "abroad" and "egypt" not in opportunity.location.lower():
            preference_score = RUBRIC["preference_fit"]
            reasons.append("Location supports abroad preference.")
        score += preference_score

        readiness_score = RUBRIC["readiness"]
        if "intern" not in opportunity.title.lower():
            readiness_score = int(RUBRIC["readiness"] * 0.6)
            reasons.append("Role may not be strictly internship-level.")
        else:
            reasons.append("Internship-level role.")
        score += readiness_score

        missing = [skill for skill in user_skills if skill not in matched_skills][:3]
        recommended_actions = [
            f"Build a project using {skill}." for skill in missing
        ] if missing else ["Polish resume with highlighted projects."]
        return OpportunityScore(
            title=opportunity.title,
            company=opportunity.company,
            location=opportunity.location,
            url=opportunity.url,
            source=opportunity.source,
            work_type=opportunity.work_type,
            score=min(score, 100),
            reasons=reasons,
            missing_skills=missing,
            recommended_actions=recommended_actions,
        )
