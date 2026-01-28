"""
Search Client - LinkedIn Only.
All job searches go through LinkedIn API with boolean queries.
"""
from __future__ import annotations

import logging
from typing import Protocol

from app.config import settings
from app.models.schemas import OpportunityRaw
from app.services.linkedin_client import (
    LinkedInSerpAPIClient,
    LinkedInMockClient,
    get_linkedin_client,
    TRACK_TITLES,
)

logger = logging.getLogger("search_client")


# Re-export for backward compatibility
__all__ = [
    "SearchClient",
    "get_search_client",
    "TRACK_TITLES",
    "EGYPTIAN_COMPANIES",
    "PLATFORM_CONFIGS",
]


# Egyptian tech companies for reference
EGYPTIAN_COMPANIES = [
    "Vodafone Egypt", "Orange Egypt", "Etisalat Egypt", "Valeo Egypt", "IBM Egypt",
    "Microsoft Egypt", "Amazon Egypt", "Google Egypt", "Meta Egypt", "Dell Egypt",
    "Swvl", "Instabug", "Fawry", "Paymob", "Noon Academy", "Vezeeta", "Elmenus",
    "Careem Egypt", "Uber Egypt", "Teleperformance Egypt", "Xceed", "ITWorx",
    "Mentor Graphics", "Synopsys Egypt", "Si-Vision", "ITIDA", "Banha Electronics",
    "Arab African International Bank Tech", "CIB Digital", "QNB Alahli Tech",
]

# Dummy for backward compatibility
PLATFORM_CONFIGS = {"linkedin": {"enabled": True}}


class SearchClient(Protocol):
    """Protocol for search clients."""
    
    def search(self, query: str, limit: int, location_preference: str = "egypt") -> list[OpportunityRaw]:
        """Search for job opportunities."""
        ...


def get_search_client() -> LinkedInSerpAPIClient | LinkedInMockClient:
    """
    Get the LinkedIn search client.
    
    Returns LinkedInSerpAPIClient if SEARCH_API_KEY is set,
    otherwise returns LinkedInMockClient for testing.
    """
    return get_linkedin_client()


def get_egyptian_companies() -> list[str]:
    """Return list of Egyptian tech companies."""
    return EGYPTIAN_COMPANIES.copy()
