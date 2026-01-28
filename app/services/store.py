from __future__ import annotations

from dataclasses import dataclass, field
from uuid import UUID

from app.models.schemas import MatchResultRun


@dataclass
class RunStore:
    runs: dict[UUID, MatchResultRun] = field(default_factory=dict)

    def save(self, run: MatchResultRun) -> None:
        self.runs[run.run_id] = run

    def get(self, run_id: UUID) -> MatchResultRun | None:
        return self.runs.get(run_id)
