from __future__ import annotations

from app.models.schemas import SkillBuckets, UserInput, UserProfile


YEAR_MAP = {
    1: "freshman",
    2: "sophomore",
    3: "junior",
    4: "senior",
    5: "graduate",
}

SOFT_SKILLS = {"communication", "teamwork", "leadership", "collaboration", "problem solving"}
TOOLS = {"python", "sql", "pandas", "tensorflow", "pytorch", "docker", "aws"}


class ProfileNormalizerAgent:
    def normalize(self, user_input: UserInput) -> UserProfile:
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
        buckets = SkillBuckets(hard=sorted(set(hard)), tools=sorted(set(tools)), soft=sorted(set(soft)))
        return UserProfile(
            year_level=year_level,
            track=user_input.track.strip().lower(),
            location_preference=user_input.preference,
            skills=buckets,
            seniority_target="intern",
        )
