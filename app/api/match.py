from __future__ import annotations

from fastapi import APIRouter

from app.graph.workflow import MatchWorkflow
from app.models.schemas import MatchResultRun, UserInput


router = APIRouter()
workflow = MatchWorkflow()


@router.post("/match", response_model=MatchResultRun)
async def match(user_input: UserInput) -> MatchResultRun:
    result = workflow.run(user_input)
    return result
