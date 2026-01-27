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
    base_url = "https://serpapi.com/search.json"

    def __init__(self, api_key: str) -> None:
        self.api_key = api_key

    def search(self, query: str, limit: int) -> list[OpportunityRaw]:
        params = {
            "engine": "google",
            "q": query,
            "api_key": self.api_key,
            "num": limit,
        }
        response = requests.get(self.base_url, params=params, timeout=20)
        response.raise_for_status()
        data = response.json()
        results = []
        for item in data.get("organic_results", [])[:limit]:
            results.append(
                OpportunityRaw(
                    title=item.get("title", "Unknown"),
                    company=item.get("source", "Unknown"),
                    location=item.get("location", ""),
                    url=item.get("link", ""),
                    snippet=item.get("snippet", ""),
                    source="serpapi",
                    posted_date=item.get("date"),
                )
            )
        return results


def get_search_client() -> SearchClient:
    if settings.search_provider.lower() == "serpapi" and settings.search_api_key:
        return SerpAPISearchClient(settings.search_api_key)
    return MockSearchClient()
