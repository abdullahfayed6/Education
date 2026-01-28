from __future__ import annotations

from app.models.schemas import OpportunityScore, UserProfile


class CoachAgent:
    def build_plan(
        self, profile: UserProfile, opportunities: list[OpportunityScore]
    ) -> dict[str, list[str]]:
        missing = []
        for opportunity in opportunities:
            missing.extend(opportunity.missing_skills)
        unique_missing = list(dict.fromkeys(missing))[:5]
        two_weeks = [
            "Review internship requirements and tailor resume.",
            "Complete 1 short course on a missing core skill.",
        ]
        one_month = [
            f"Build a portfolio project using {skill}." for skill in unique_missing
        ] or ["Build a portfolio project aligned with your track."]
        return {
            "next_2_weeks": two_weeks,
            "next_1_month": one_month,
            "notes": [f"Track focus: {profile.track}."]
        }
