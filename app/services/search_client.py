from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

import requests

from app.config import settings
from app.models.schemas import OpportunityRaw


@dataclass(frozen=True)
class SearchResult:
    title: str
    company: str
    location: str
    url: str
    snippet: str
    source: str
    posted_date: str | None = None


class SearchClient(Protocol):
    def search(self, query: str, limit: int) -> list[OpportunityRaw]:
        ...


class MockSearchClient:
    def search(self, query: str, limit: int) -> list[OpportunityRaw]:
        results = []
        for index in range(limit):
            results.append(
                OpportunityRaw(
                    title=f"Data Intern {index + 1}",
                    company=f"ExampleCo {index % 5}",
                    location="Cairo, Egypt" if index % 2 == 0 else "Remote",
                    url=f"https://example.com/jobs/{index}",
                    snippet=f"Internship role related to {query}.",
                    source="mock",
                    posted_date=None,
                )
            )
        return results


class SerpAPISearchClient:
    """SerpAPI client using Google Jobs API for real internship listings."""
    
    base_url = "https://serpapi.com/search.json"

    def __init__(self, api_key: str) -> None:
        self.api_key = api_key

    def search(self, query: str, limit: int) -> list[OpportunityRaw]:
        # Use Google Jobs engine for better job listings
        params = {
            "engine": "google_jobs",
            "q": query,
            "api_key": self.api_key,
            "num": limit,
        }
        
        try:
            response = requests.get(self.base_url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            results = []
            jobs = data.get("jobs_results", [])
            
            for item in jobs[:limit]:
                # Extract company and location
                company = item.get("company_name", "Unknown")
                location = item.get("location", "")
                
                # Get the apply link or use the job listing link
                apply_options = item.get("apply_options", [])
                url = apply_options[0].get("link", "") if apply_options else item.get("share_link", "")
                
                # Get job highlights for description
                highlights = item.get("job_highlights", [])
                description_parts = []
                for highlight in highlights:
                    items = highlight.get("items", [])
                    description_parts.extend(items)
                description = " | ".join(description_parts[:3]) if description_parts else item.get("description", "")[:500]
                
                results.append(
                    OpportunityRaw(
                        title=item.get("title", "Unknown"),
                        company=company,
                        location=location,
                        url=url,
                        snippet=description,
                        source="serpapi",
                        posted_date=item.get("detected_extensions", {}).get("posted_at"),
                    )
                )
            
            return results
            
        except requests.RequestException as e:
            print(f"SerpAPI error: {e}")
            return []


def get_search_client() -> SearchClient:
    if settings.search_provider.lower() == "serpapi" and settings.search_api_key:
        return SerpAPISearchClient(settings.search_api_key)
    return MockSearchClient()

