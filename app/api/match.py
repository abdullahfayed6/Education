from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException

from app.graph.workflow import MatchWorkflow
from app.models.schemas import MatchResultRun, UserInput
from app.services.store import RunStore


router = APIRouter()
workflow = MatchWorkflow()
store = RunStore()


@router.post("/match", response_model=MatchResultRun)
async def match(user_input: UserInput) -> MatchResultRun:
    result = workflow.run(user_input)
    store.save(result)
    return result


@router.get("/match/{run_id}", response_model=MatchResultRun)
async def get_match(run_id: str) -> MatchResultRun:
    try:
        run_uuid = UUID(run_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid run_id") from exc
    stored = store.get(run_uuid)
    if not stored:
        raise HTTPException(status_code=404, detail="Run not found")
    return stored
