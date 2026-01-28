"""FastAPI endpoints for the interview system."""
from __future__ import annotations

import logging
from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from app.models.interview_schemas import (
    FinalReport,
    InterviewConfig,
    InterviewState,
    SessionStatusResponse,
    StartInterviewRequest,
    StartInterviewResponse,
    SubmitAnswerRequest,
    SubmitAnswerResponse,
)
from app.services.session_store import session_store

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/interview", tags=["interview"])


@router.post("/start", response_model=StartInterviewResponse)
async def start_interview(request: StartInterviewRequest) -> StartInterviewResponse:
    """
    Start a new interview session.
    
    Creates a new interview session with the provided configuration and returns
    the first interview question.
    """
    try:
        # Create new session
        orchestrator = session_store.create_session(
            user_id=request.user_id,
            config=request.config,
        )
        
        # Generate first question
        first_question = await orchestrator.start_interview()
        
        logger.info(f"Started interview session {orchestrator.session_id} for user {request.user_id}")
        
        return StartInterviewResponse(
            session_id=orchestrator.session_id,
            first_question=first_question,
            state=orchestrator.current_state,
            difficulty=orchestrator.session.current_difficulty,
        )
    
    except Exception as e:
        logger.error(f"Error starting interview: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start interview: {str(e)}"
        )


@router.post("/answer", response_model=SubmitAnswerResponse)
async def submit_answer(request: SubmitAnswerRequest) -> SubmitAnswerResponse:
    """
    Submit an answer to the current interview question.
    
    Processes the answer through the evaluation pipeline and returns:
    - Evaluation of the answer
    - Feedback for improvement
    - Difficulty adjustment
    - Next question (if interview continues)
    """
    # Get session
    orchestrator = session_store.get_session(request.session_id)
    if not orchestrator:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {request.session_id} not found"
        )
    
    if orchestrator.is_complete:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Interview session is already complete"
        )
    
    try:
        # Process the answer
        result = await orchestrator.process_answer(
            question=request.question,
            answer=request.answer,
        )
        
        logger.info(f"Processed answer for session {request.session_id}, state: {result['next_state']}")
        
        return SubmitAnswerResponse(
            evaluation=result["evaluation"],
            feedback=result["feedback"],
            difficulty_adjustment=result["difficulty_adjustment"],
            next_state=result["next_state"],
            next_question=result["next_question"],
            is_complete=result["is_complete"],
        )
    
    except Exception as e:
        logger.error(f"Error processing answer: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process answer: {str(e)}"
        )


@router.get("/{session_id}", response_model=SessionStatusResponse)
async def get_session_status(session_id: UUID) -> SessionStatusResponse:
    """
    Get the current status of an interview session.
    
    Returns session state, progress, and performance metrics.
    """
    orchestrator = session_store.get_session(session_id)
    if not orchestrator:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found"
        )
    
    status_info = orchestrator.get_session_status()
    
    return SessionStatusResponse(
        session_id=status_info["session_id"],
        current_state=status_info["current_state"],
        questions_asked=status_info["questions_asked"],
        average_score=status_info["average_score"],
        current_difficulty=status_info["current_difficulty"],
        is_complete=status_info["is_complete"],
        performance_trend=status_info["performance_trend"],
    )


@router.get("/{session_id}/report", response_model=FinalReport)
async def get_final_report(session_id: UUID) -> FinalReport:
    """
    Get the final interview report.
    
    Generates a comprehensive assessment including:
    - Technical level estimate
    - Communication profile
    - Hiring recommendations
    - Improvement plan
    """
    # Check for cached report first
    cached_report = session_store.get_report(session_id)
    if cached_report:
        return cached_report
    
    # Get session
    orchestrator = session_store.get_session(session_id)
    if not orchestrator:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found"
        )
    
    if not orchestrator.is_complete:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Interview is not yet complete. Cannot generate report."
        )
    
    try:
        # Generate report
        report = await orchestrator.generate_final_report()
        
        # Cache the report
        session_store.store_report(session_id, report)
        
        logger.info(f"Generated final report for session {session_id}")
        
        return report
    
    except Exception as e:
        logger.error(f"Error generating report: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate report: {str(e)}"
        )


@router.delete("/{session_id}")
async def delete_session(session_id: UUID) -> dict:
    """
    Delete an interview session.
    
    Removes the session and any associated data.
    """
    if session_store.remove_session(session_id):
        logger.info(f"Deleted session {session_id}")
        return {"message": f"Session {session_id} deleted successfully"}
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found"
        )


@router.get("/")
async def list_sessions(user_id: str | None = None) -> dict:
    """
    List all active interview sessions.
    
    Optionally filter by user_id.
    """
    sessions = session_store.list_sessions(user_id)
    return {
        "sessions": sessions,
        "total": len(sessions),
    }


# Synchronous endpoints for testing
@router.post("/start-sync", response_model=StartInterviewResponse)
def start_interview_sync(request: StartInterviewRequest) -> StartInterviewResponse:
    """Synchronous version of start_interview for testing."""
    try:
        orchestrator = session_store.create_session(
            user_id=request.user_id,
            config=request.config,
        )
        
        first_question = orchestrator.start_interview_sync()
        
        return StartInterviewResponse(
            session_id=orchestrator.session_id,
            first_question=first_question,
            state=orchestrator.current_state,
            difficulty=orchestrator.session.current_difficulty,
        )
    
    except Exception as e:
        logger.error(f"Error starting interview: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start interview: {str(e)}"
        )


@router.post("/answer-sync", response_model=SubmitAnswerResponse)
def submit_answer_sync(request: SubmitAnswerRequest) -> SubmitAnswerResponse:
    """Synchronous version of submit_answer for testing."""
    orchestrator = session_store.get_session(request.session_id)
    if not orchestrator:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {request.session_id} not found"
        )
    
    if orchestrator.is_complete:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Interview session is already complete"
        )
    
    try:
        result = orchestrator.process_answer_sync(
            question=request.question,
            answer=request.answer,
        )
        
        return SubmitAnswerResponse(
            evaluation=result["evaluation"],
            feedback=result["feedback"],
            difficulty_adjustment=result["difficulty_adjustment"],
            next_state=result["next_state"],
            next_question=result["next_question"],
            is_complete=result["is_complete"],
        )
    
    except Exception as e:
        logger.error(f"Error processing answer: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process answer: {str(e)}"
        )
