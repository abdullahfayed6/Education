from app.agents.profile_normalizer import ProfileNormalizerAgent
from app.models.schemas import UserInput


def test_profile_normalization() -> None:
    agent = ProfileNormalizerAgent()
    user_input = UserInput(
        academic_year=3,
        preference="remote",
        track="data_scientist",
        skills=["Python", "Communication", "SQL"],
    )
    profile = agent.normalize(user_input)
    assert profile.year_level == "junior"
    assert "python" in profile.skills.tools
    assert "communication" in profile.skills.soft
