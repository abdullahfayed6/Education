from __future__ import annotations

import logging

from fastapi import FastAPI

from app.api.match import router as match_router

logging.basicConfig(level=logging.INFO)

app = FastAPI(title="Internship Opportunity Matcher")
app.include_router(match_router)
