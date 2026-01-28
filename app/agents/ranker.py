from __future__ import annotations

from app.config import settings
from app.models.schemas import OpportunityScore


class RankerAgent:
    def rank(self, scored: list[OpportunityScore]) -> list[OpportunityScore]:
        sorted_items = sorted(scored, key=lambda item: item.score, reverse=True)
        top: list[OpportunityScore] = []
        company_counts: dict[str, int] = {}
        for item in sorted_items:
            count = company_counts.get(item.company.lower(), 0)
            if count >= 2 and len(top) < settings.top_k:
                continue
            top.append(item)
            company_counts[item.company.lower()] = count + 1
            if len(top) >= settings.top_k:
                break
        return top
