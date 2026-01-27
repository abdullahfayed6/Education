from __future__ import annotations

from app.config import settings
from app.models.schemas import OpportunityRaw, QuerySpec
from app.services.cache import InMemoryCache
from app.services.search_client import get_search_client


class RetrievalAgent:
    def __init__(self, cache: InMemoryCache) -> None:
        self.cache = cache
        self.client = get_search_client()

    def retrieve(self, queries: list[QuerySpec]) -> list[OpportunityRaw]:
        results: list[OpportunityRaw] = []
        for query in queries:
            cache_key = f"retrieval:{query.query}"
            cached = self.cache.get(cache_key)
            if cached:
                results.extend(cached)
                continue
            fetched = self.client.search(query.query, settings.max_results)
            self.cache.set(cache_key, fetched, ttl_seconds=3600)
            results.extend(fetched)
        if len(results) < settings.max_results:
            fallback_query = "internship opportunities"
            fallback_key = f"retrieval:{fallback_query}"
            cached = self.cache.get(fallback_key)
            if cached:
                results.extend(cached)
            else:
                fetched = self.client.search(fallback_query, settings.max_results)
                self.cache.set(fallback_key, fetched, ttl_seconds=3600)
                results.extend(fetched)
        return results[: settings.max_results]
