"""
OpenAI Client for AI-powered job matching reasons and scoring.
Generates personalized explanations for why a job matches a candidate.
"""
from __future__ import annotations

import json
import logging
from typing import Any

import openai
import requests

from app.config import settings
from app.models.schemas import OpportunityClean, OpportunityScore, UserProfile

logger = logging.getLogger("openai_client")


class OpenAIClient:
    """OpenAI client for AI-powered job matching and scoring."""
    
    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key or settings.openai_api_key
        self.client = None
        if self.api_key:
            self.client = openai.OpenAI(api_key=self.api_key)
        self.model = "gpt-4o-mini"  # Fast and cost-effective
    
    def score_opportunity(
        self, profile: UserProfile, opportunity: OpportunityClean, rubric: dict[str, int]
    ) -> OpportunityScore | None:
        """Score opportunity with AI-powered reasons and actions."""
        if not self.api_key:
            return None
        system_prompt = (
            "Return valid JSON only. Follow the schema exactly. Score from 0-100."
        )
        payload = {
            "model": self.model,
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
    
    def generate_match_reasons(
        self,
        job_title: str,
        company: str,
        job_description: str,
        user_track: str,
        user_skills: list[str],
        user_year: str,
        location_preference: str,
        job_location: str,
        score: int,
    ) -> list[str]:
        """
        Generate AI-powered personalized reasons for why this job matches the user.
        
        Returns a list of 3-5 concise, specific reasons.
        """
        if not self.api_key:
            return self._fallback_reasons(score, job_title, company)
            
        prompt = f"""You are a career advisor analyzing a job match for a student.

**Student Profile:**
- Track/Major: {user_track}
- Skills: {', '.join(user_skills) if user_skills else 'Not specified'}
- Academic Year: {user_year}
- Location Preference: {location_preference}

**Job Details:**
- Title: {job_title}
- Company: {company}
- Location: {job_location}
- Description: {job_description[:500] if job_description else 'No description available'}

**Match Score: {score}/100**

Write 3-5 short, specific reasons explaining why this job is a good match for this student. 
Be specific about skills, company, and role alignment.
Use emojis sparingly (1-2 max).
Each reason should be 1 sentence, direct and actionable.

Return ONLY a JSON array of strings, like:
["Reason 1", "Reason 2", "Reason 3"]
"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful career advisor. Return only valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=300,
            )
            
            content = response.choices[0].message.content.strip()
            
            # Parse JSON response
            # Handle potential markdown code blocks
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
                content = content.strip()
            
            reasons = json.loads(content)
            
            if isinstance(reasons, list) and all(isinstance(r, str) for r in reasons):
                return reasons[:5]  # Max 5 reasons
            
            logger.warning("Invalid AI response format, using fallback")
            return self._fallback_reasons(score, job_title, company)
            
        except Exception as e:
            logger.error(f"OpenAI error: {e}")
            return self._fallback_reasons(score, job_title, company)
    
    def _fallback_reasons(self, score: int, job_title: str, company: str) -> list[str]:
        """Fallback reasons if AI fails."""
        if score >= 70:
            return [
                f"Strong alignment with the {job_title} role.",
                f"{company} offers great learning opportunities.",
                "Your skills match the job requirements well."
            ]
        elif score >= 50:
            return [
                f"Good potential match for {job_title}.",
                "This role can help you grow your skills.",
                f"Consider applying to {company}."
            ]
        else:
            return [
                "This is an entry-level opportunity.",
                "Could be a stepping stone for your career.",
            ]


def get_openai_client() -> OpenAIClient | None:
    """Get OpenAI client if API key is configured."""
    if settings.openai_api_key:
        return OpenAIClient(settings.openai_api_key)
    logger.warning("OpenAI API key not configured")
    return None
