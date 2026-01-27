from app.agents.ranker import RankerAgent
from app.models.schemas import OpportunityScore


def test_ranker_diversity() -> None:
    agent = RankerAgent()
    scored = [
        OpportunityScore(
            title=f"Role {i}",
            company="SameCo" if i < 4 else "OtherCo",
            location="Remote",
            url=f"https://example.com/{i}",
            source="mock",
            work_type="Remote",
            score=100 - i,
            reasons=["ok"],
            missing_skills=[],
            recommended_actions=[],
        )
        for i in range(6)
    ]
    ranked = agent.rank(scored)
    assert len(ranked) == 5
    assert sum(1 for item in ranked if item.company == "SameCo") <= 2
