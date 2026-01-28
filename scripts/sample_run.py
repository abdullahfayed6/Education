from app.graph.workflow import MatchWorkflow
from app.models.schemas import UserInput


def main() -> None:
    workflow = MatchWorkflow()
    user_input = UserInput(
        academic_year=3,
        preference="remote",
        track="data_scientist",
        skills=["python", "pandas", "sql", "ml basics"],
        notes="Interested in healthtech roles",
    )
    result = workflow.run(user_input)
    print(result.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
