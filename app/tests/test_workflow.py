from app.graph.workflow import MatchWorkflow
from app.models.schemas import UserInput


def test_workflow_run() -> None:
    workflow = MatchWorkflow()
    user_input = UserInput(
        academic_year=2,
        preference="egypt",
        track="backend",
        skills=["python", "sql"],
        notes="Interested in fintech",
    )
    result = workflow.run(user_input)
    assert result.generated_queries
    assert result.ranked_top5
