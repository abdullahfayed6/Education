from __future__ import annotations

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.match import router as match_router
from app.api.interview import router as interview_router

logging.basicConfig(level=logging.INFO)

app = FastAPI(
    title="Education Platform - Interview & Opportunity Matcher",
    description="Multi-Agent Interview System with Adaptive Difficulty and Comprehensive Reporting",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(match_router)
app.include_router(interview_router)


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Education Platform API",
        "endpoints": {
            "interview": "/api/interview",
            "match": "/api/match",
            "docs": "/docs",
        },
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}
