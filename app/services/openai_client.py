from __future__ import annotations

import json

import requests

from app.config import settings
from app.models.schemas import OpportunityClean, OpportunityScore, UserProfile


class OpenAIClient:
    def __init__(self) -> None:
        self.api_key = settings.openai_api_key

    def score_opportunity(
        self, profile: UserProfile, opportunity: OpportunityClean, rubric: dict[str, int]
    ) -> OpportunityScore | None:
        if not self.api_key:
            return None
        system_prompt = (
            "Return valid JSON only. Follow the schema exactly. Score from 0-100."
        )
        payload = {
            "model": "gpt-4o-mini",
            "temperature": 0.2,
            "messages": [
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": json.dumps(
                        {
                            "profile": profile.model_dump(),
                            "opportunity": opportunity.model_dump(),
                            "rubric": rubric,
                        }
                    ),
                },
            ],
        }
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {self.api_key}"},
            json=payload,
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()
        content = data["choices"][0]["message"]["content"]
        parsed = json.loads(content)
        return OpportunityScore(
            title=opportunity.title,
            company=opportunity.company,
            location=opportunity.location,
            url=opportunity.url,
            source=opportunity.source,
            work_type=opportunity.work_type,
            score=parsed["score"],
            reasons=parsed["reasons"],
            missing_skills=parsed["missing_skills"],
            recommended_actions=parsed["recommended_actions"],
        )
