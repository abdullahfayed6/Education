from __future__ import annotations

import logging
from datetime import datetime
from uuid import uuid4

from app.agents.cleaner import OpportunityCleanerAgent
from app.agents.coach import CoachAgent
from app.agents.profile_normalizer import ProfileNormalizerAgent
from app.agents.query_builder import QueryBuilderAgent
from app.agents.ranker import RankerAgent
from app.agents.retriever import RetrievalAgent
from app.agents.scorer import ScoringAgent
from app.models.schemas import MatchResultRun, UserInput
from app.services.cache import InMemoryCache


logger = logging.getLogger("matcher")


class MatchWorkflow:
    def __init__(self) -> None:
        self.cache = InMemoryCache()
        self.profile_agent = ProfileNormalizerAgent()
        self.query_agent = QueryBuilderAgent()
        self.retrieval_agent = RetrievalAgent(self.cache)
        self.cleaner_agent = OpportunityCleanerAgent()
        self.scoring_agent = ScoringAgent()
        self.ranker_agent = RankerAgent()
        self.coach_agent = CoachAgent()

    def run(self, user_input: UserInput) -> MatchResultRun:
        profile = self.profile_agent.normalize(user_input)
        logger.info("Profile normalized", extra={"profile": profile.model_dump()})

        queries = self.query_agent.build(profile)
        logger.info("Queries built", extra={"queries": [q.model_dump() for q in queries]})

        raw_opportunities = self.retrieval_agent.retrieve(queries)
        logger.info("Retrieved", extra={"count": len(raw_opportunities)})

        clean_opportunities = self.cleaner_agent.clean(raw_opportunities)
        logger.info("Cleaned", extra={"count": len(clean_opportunities)})

        scored = [self.scoring_agent.score(profile, opp) for opp in clean_opportunities]
        logger.info("Scored", extra={"count": len(scored)})

        ranked = self.ranker_agent.rank(scored)
        logger.info("Ranked", extra={"count": len(ranked)})

        coach_plan = self.coach_agent.build_plan(profile, ranked)
        logger.info("Coach plan generated")

        return MatchResultRun(
            run_id=uuid4(),
            created_at=datetime.utcnow(),
            normalized_profile=profile,
            generated_queries=queries,
            opportunities_top20=clean_opportunities,
            ranked_top5=ranked,
            coach_plan=coach_plan,
        )
