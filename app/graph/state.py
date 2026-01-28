"""LangGraph state definition for the matching workflow."""
from __future__ import annotations

from typing import TypedDict

from app.models.schemas import (
    MatchResultRun,
    OpportunityClean,
    OpportunityRaw,
    OpportunityScore,
    QuerySpec,
    UserInput,
    UserProfile,
)


class MatchState(TypedDict, total=False):
    """State that flows through the LangGraph workflow."""
    # Input
    user_input: UserInput
    
    # Processed data
    profile: UserProfile
    queries: list[QuerySpec]
    raw_opportunities: list[OpportunityRaw]
    clean_opportunities: list[OpportunityClean]
    scored_opportunities: list[OpportunityScore]
    ranked_opportunities: list[OpportunityScore]
    
    # Output
    result: MatchResultRun
