"""FastAPI endpoints for the Career Translator Agent."""
from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse

from app.agents.career_translator import CareerTranslatorAgent, get_career_translator
from app.models.career_schemas import (
    CareerTranslation,
    LectureInput,
    TranslateLectureRequest,
    TranslateLectureResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/career", tags=["career-translator"])


@router.post(
    "/translate",
    response_model=TranslateLectureResponse,
    summary="Translate lecture to career value",
    description="Converts academic lecture topics into industry-relevant content including use cases, tasks, and career impact."
)
async def translate_lecture(request: TranslateLectureRequest) -> TranslateLectureResponse:
    """
    Translate a lecture topic into career-relevant industry content.
    
    This endpoint takes a lecture topic and optional detailed content,
    then returns structured JSON with:
    - Real-world relevance
    - Industry use cases
    - Company-style practical tasks
    - Skills developed
    - Career impact
    - Advanced challenges
    """
    try:
        translator = get_career_translator()
        
        lecture_input = LectureInput(
            lecture_topic=request.lecture_topic,
            lecture_text=request.lecture_text,
        )
        
        translation = await translator.translate(lecture_input)
        
        logger.info(f"Translated lecture: {request.lecture_topic}")
        
        return TranslateLectureResponse(
            success=True,
            data=translation,
        )
    
    except Exception as e:
        logger.error(f"Error translating lecture: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to translate lecture: {str(e)}"
        )


@router.post(
    "/translate/raw",
    response_model=CareerTranslation,
    summary="Translate lecture - raw JSON output",
    description="Returns raw CareerTranslation JSON without wrapper for direct consumption by other agents."
)
async def translate_lecture_raw(request: TranslateLectureRequest) -> CareerTranslation:
    """
    Translate a lecture topic and return raw JSON output.
    
    This endpoint is optimized for agent-to-agent communication,
    returning the CareerTranslation directly without a wrapper.
    """
    try:
        translator = get_career_translator()
        
        lecture_input = LectureInput(
            lecture_topic=request.lecture_topic,
            lecture_text=request.lecture_text,
        )
        
        translation = await translator.translate(lecture_input)
        
        return translation
    
    except Exception as e:
        logger.error(f"Error translating lecture: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to translate lecture: {str(e)}"
        )


@router.post(
    "/translate/sync",
    response_model=TranslateLectureResponse,
    summary="Translate lecture (synchronous)",
    description="Synchronous version for testing and simple integrations."
)
def translate_lecture_sync(request: TranslateLectureRequest) -> TranslateLectureResponse:
    """Synchronous version of translate_lecture for testing."""
    try:
        translator = get_career_translator()
        
        lecture_input = LectureInput(
            lecture_topic=request.lecture_topic,
            lecture_text=request.lecture_text,
        )
        
        translation = translator.translate_sync(lecture_input)
        
        return TranslateLectureResponse(
            success=True,
            data=translation,
        )
    
    except Exception as e:
        logger.error(f"Error translating lecture: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to translate lecture: {str(e)}"
        )


@router.get(
    "/health",
    summary="Health check",
    description="Check if the Career Translator Agent is operational."
)
async def health_check() -> dict:
    """Health check for the Career Translator service."""
    return {
        "status": "healthy",
        "service": "CareerTranslatorAgent",
        "version": "1.0.0"
    }


@router.post(
    "/batch",
    response_model=list[CareerTranslation],
    summary="Batch translate lectures",
    description="Translate multiple lecture topics in a single request."
)
async def batch_translate(requests: list[TranslateLectureRequest]) -> list[CareerTranslation]:
    """
    Batch translate multiple lecture topics.
    
    Useful for processing entire course syllabi or multiple topics at once.
    """
    try:
        translator = get_career_translator()
        translations = []
        
        for req in requests:
            lecture_input = LectureInput(
                lecture_topic=req.lecture_topic,
                lecture_text=req.lecture_text,
            )
            translation = await translator.translate(lecture_input)
            translations.append(translation)
        
        logger.info(f"Batch translated {len(translations)} lectures")
        
        return translations
    
    except Exception as e:
        logger.error(f"Error in batch translation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to batch translate: {str(e)}"
        )
