"""
Search Client - Multiple providers including LinkedIn.
Supports SerpAPI, LinkedIn, and Mock for testing.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Protocol

import requests

from app.config import settings
from app.models.schemas import OpportunityRaw

logger = logging.getLogger("search_client")


# Egyptian tech companies for reference
EGYPTIAN_COMPANIES = [
    "Vodafone Egypt", "Orange Egypt", "Etisalat Egypt", "Valeo Egypt", "IBM Egypt",
    "Microsoft Egypt", "Amazon Egypt", "Google Egypt", "Meta Egypt", "Dell Egypt",
    "Swvl", "Instabug", "Fawry", "Paymob", "Noon Academy", "Vezeeta", "Elmenus",
    "Careem Egypt", "Uber Egypt", "Teleperformance Egypt", "Xceed", "ITWorx",
    "Mentor Graphics", "Synopsys Egypt", "Si-Vision", "ITIDA", "Banha Electronics",
    "Arab African International Bank Tech", "CIB Digital", "QNB Alahli Tech",
]


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
    def search(self, query: str, limit: int, location_preference: str) -> list[OpportunityRaw]:
        ...


class MockSearchClient:
    def search(self, query: str, limit: int, location_preference: str = "egypt") -> list[OpportunityRaw]:
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

    def search(self, query: str, limit: int, location_preference: str = "egypt") -> list[OpportunityRaw]:
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
            logger.error(f"SerpAPI error: {e}")
            return []


def get_search_client() -> SearchClient:
    """
    Get the appropriate search client based on configuration.
    
    Returns SerpAPISearchClient if configured, otherwise MockSearchClient.
    """
    if settings.search_provider.lower() == "serpapi" and settings.search_api_key:
        return SerpAPISearchClient(settings.search_api_key)
    return MockSearchClient()


def get_egyptian_companies() -> list[str]:
    """Return list of Egyptian tech companies."""
    return EGYPTIAN_COMPANIES.copy()
