from __future__ import annotations

from app.models.schemas import OpportunityClean, OpportunityRaw


class OpportunityCleanerAgent:
    def clean(self, opportunities: list[OpportunityRaw]) -> list[OpportunityClean]:
        seen = set()
        cleaned = []
        for item in opportunities:
            key = (item.title.lower(), item.company.lower(), item.url)
            if key in seen:
                continue
            seen.add(key)
            cleaned.append(
                OpportunityClean(
                    title=item.title.strip(),
                    company=item.company.strip(),
                    location=item.location.strip() or "Unknown",
                    url=item.url,
                    source=item.source,
                    description=item.snippet or "",
                    work_type=self._infer_work_type(item.location),
                    posted_date=item.posted_date,
                )
            )
        return cleaned

    def _infer_work_type(self, location: str) -> str | None:
        location_lower = location.lower()
        if "remote" in location_lower:
            return "Remote"
        if "hybrid" in location_lower:
            return "Hybrid"
        if location:
            return "On-site"
        return None
