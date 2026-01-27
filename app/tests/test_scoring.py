from app.agents.scorer import ScoringAgent
from app.models.schemas import OpportunityClean, UserProfile, SkillBuckets


def test_scoring_schema() -> None:
    agent = ScoringAgent()
    profile = UserProfile(
        year_level="junior",
        track="data_scientist",
        location_preference="remote",
        skills=SkillBuckets(hard=["ml"], tools=["python"], soft=[]),
        seniority_target="intern",
    )
    opportunity = OpportunityClean(
        title="Data Science Intern",
        company="ExampleCo",
        location="Remote",
        url="https://example.com",
        source="mock",
        description="Work with python and ML models.",
        work_type="Remote",
    )
    scored = agent.score(profile, opportunity)
    assert 0 <= scored.score <= 100
    assert scored.reasons
