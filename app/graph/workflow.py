"""LangGraph workflow for matching students with internship opportunities."""
from __future__ import annotations

import logging

from langgraph.graph import StateGraph, START, END

from app.graph.state import MatchState
from app.graph.nodes import (
    normalize_profile,
    build_queries,
    retrieve_opportunities,
    clean_opportunities,
    score_opportunities,
    rank_opportunities,
    build_coach_plan,
    build_result,
)
from app.models.schemas import MatchResultRun, UserInput

logger = logging.getLogger("matcher")


def create_match_graph() -> StateGraph:
    """Create and return the compiled LangGraph workflow."""
    
    # Build the graph
    builder = StateGraph(MatchState)
    
    # Add nodes
    builder.add_node("normalize_profile", normalize_profile)
    builder.add_node("build_queries", build_queries)
    builder.add_node("retrieve_opportunities", retrieve_opportunities)
    builder.add_node("clean_opportunities", clean_opportunities)
    builder.add_node("score_opportunities", score_opportunities)
    builder.add_node("rank_opportunities", rank_opportunities)
    builder.add_node("build_coach_plan", build_coach_plan)
    builder.add_node("build_result", build_result)
    
    # Define edges (linear flow)
    builder.add_edge(START, "normalize_profile")
    builder.add_edge("normalize_profile", "build_queries")
    builder.add_edge("build_queries", "retrieve_opportunities")
    builder.add_edge("retrieve_opportunities", "clean_opportunities")
    builder.add_edge("clean_opportunities", "score_opportunities")
    builder.add_edge("score_opportunities", "rank_opportunities")
    builder.add_edge("rank_opportunities", "build_coach_plan")
    builder.add_edge("build_coach_plan", "build_result")
    builder.add_edge("build_result", END)
    
    return builder.compile()


# Create the compiled graph
match_graph = create_match_graph()


class MatchWorkflow:
    """Wrapper class for backward compatibility with the API."""
    
    def __init__(self) -> None:
        self.graph = match_graph
    
    def run(self, user_input: UserInput) -> MatchResultRun:
        """Execute the matching workflow."""
        initial_state: MatchState = {"user_input": user_input}
        
        # Run the graph
        final_state = self.graph.invoke(initial_state)
        
        return final_state["result"]
