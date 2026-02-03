"""
Global Exception Handler Middleware

Provides centralized error handling with:
- Consistent error responses
- Detailed logging
- Cosmos DB specific error handling
- Production-safe error messages
"""

from __future__ import annotations

import logging
import traceback
from typing import Callable

from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from azure.cosmos import exceptions as cosmos_exceptions

from src.config.settings import settings

logger = logging.getLogger(__name__)


class ErrorResponse:
    """Standardized error response format."""
    
    def __init__(
        self,
        error: str,
        message: str,
        status_code: int,
        details: dict | None = None
    ):
        self.error = error
        self.message = message
        self.status_code = status_code
        self.details = details or {}
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        response = {
            "error": self.error,
            "message": self.message,
            "status_code": self.status_code
        }
        
        if self.details and settings.debug:
            response["details"] = self.details
        
        return response


async def exception_handler_middleware(
    request: Request,
    call_next: Callable
) -> Response:
    """
    Global exception handler middleware.
    
    Catches all unhandled exceptions and returns consistent error responses.
    """
    try:
        response = await call_next(request)
        return response
    
    except StarletteHTTPException as exc:
        # HTTP exceptions from FastAPI
        return JSONResponse(
            status_code=exc.status_code,
            content=ErrorResponse(
                error="HTTP_ERROR",
                message=exc.detail,
                status_code=exc.status_code
            ).to_dict()
        )
    
    except RequestValidationError as exc:
        # Pydantic validation errors
        logger.warning(f"Validation error: {exc.errors()}")
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=ErrorResponse(
                error="VALIDATION_ERROR",
                message="Request validation failed",
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                details={"errors": exc.errors()}
            ).to_dict()
        )
    
    except cosmos_exceptions.CosmosResourceNotFoundError as exc:
        # Cosmos DB: Resource not found
        logger.info(f"Resource not found: {exc.message}")
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=ErrorResponse(
                error="RESOURCE_NOT_FOUND",
                message="The requested resource was not found",
                status_code=status.HTTP_404_NOT_FOUND
            ).to_dict()
        )
    
    except cosmos_exceptions.CosmosResourceExistsError as exc:
        # Cosmos DB: Resource already exists
        logger.warning(f"Resource conflict: {exc.message}")
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content=ErrorResponse(
                error="RESOURCE_EXISTS",
                message="Resource already exists",
                status_code=status.HTTP_409_CONFLICT
            ).to_dict()
        )
    
    except cosmos_exceptions.CosmosHttpResponseError as exc:
        # Generic Cosmos DB errors
        logger.error(f"Cosmos DB error: Status {exc.status_code} - {exc.message}")
        
        # Handle rate limiting
        if exc.status_code == 429:
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content=ErrorResponse(
                    error="RATE_LIMITED",
                    message="Too many requests. Please try again later.",
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    details={"retry_after_ms": exc.headers.get("x-ms-retry-after-ms")}
                ).to_dict(),
                headers={"Retry-After": exc.headers.get("x-ms-retry-after-ms", "1000")}
            )
        
        # Generic database error
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=ErrorResponse(
                error="DATABASE_ERROR",
                message="Database operation failed" if settings.is_production else str(exc),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            ).to_dict()
        )
    
    except ValueError as exc:
        # Value errors (business logic validation)
        logger.warning(f"Value error: {exc}")
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=ErrorResponse(
                error="INVALID_VALUE",
                message=str(exc),
                status_code=status.HTTP_400_BAD_REQUEST
            ).to_dict()
        )
    
    except Exception as exc:
        # Unexpected errors
        logger.error(
            f"Unhandled exception: {exc}\n{traceback.format_exc()}",
            exc_info=True
        )
        
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=ErrorResponse(
                error="INTERNAL_SERVER_ERROR",
                message="An unexpected error occurred" if settings.is_production else str(exc),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                details={"traceback": traceback.format_exc()} if settings.debug else {}
            ).to_dict()
        )


def setup_exception_handlers(app):
    """
    Setup custom exception handlers for FastAPI app.
    
    Args:
        app: FastAPI application instance
    """
    
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content=ErrorResponse(
                error="HTTP_ERROR",
                message=exc.detail,
                status_code=exc.status_code
            ).to_dict()
        )
    
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=ErrorResponse(
                error="VALIDATION_ERROR",
                message="Request validation failed",
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                details={"errors": exc.errors()}
            ).to_dict()
        )
    
    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception):
        logger.error(f"Unhandled exception: {exc}", exc_info=True)
        
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=ErrorResponse(
                error="INTERNAL_SERVER_ERROR",
                message="An unexpected error occurred" if settings.is_production else str(exc),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            ).to_dict()
        )
