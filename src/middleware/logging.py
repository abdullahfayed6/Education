"""
Structured Logging Middleware

Provides:
- Request/response logging
- Performance monitoring
- Correlation IDs
- Structured JSON logging
"""

from __future__ import annotations

import logging
import time
import uuid
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from src.config.settings import settings

logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for request/response logging with performance tracking."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Log request and response with timing information.
        
        Args:
            request: Incoming request
            call_next: Next middleware/handler
            
        Returns:
            Response
        """
        # Generate correlation ID
        correlation_id = str(uuid.uuid4())
        request.state.correlation_id = correlation_id
        
        # Start timer
        start_time = time.time()
        
        # Log request
        logger.info(
            "Request started",
            extra={
                "correlation_id": correlation_id,
                "method": request.method,
                "path": request.url.path,
                "query_params": dict(request.query_params),
                "client_host": request.client.host if request.client else None,
                "user_agent": request.headers.get("user-agent")
            }
        )
        
        # Process request
        try:
            response = await call_next(request)
            
            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000
            
            # Log response
            logger.info(
                "Request completed",
                extra={
                    "correlation_id": correlation_id,
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "duration_ms": round(duration_ms, 2)
                }
            )
            
            # Add correlation ID to response headers
            response.headers["X-Correlation-ID"] = correlation_id
            response.headers["X-Response-Time"] = f"{duration_ms:.2f}ms"
            
            # Warn on slow requests
            if duration_ms > 1000:  # 1 second threshold
                logger.warning(
                    f"Slow request detected: {request.method} {request.url.path} "
                    f"took {duration_ms:.2f}ms",
                    extra={
                        "correlation_id": correlation_id,
                        "duration_ms": duration_ms
                    }
                )
            
            return response
            
        except Exception as exc:
            duration_ms = (time.time() - start_time) * 1000
            
            logger.error(
                "Request failed",
                extra={
                    "correlation_id": correlation_id,
                    "method": request.method,
                    "path": request.url.path,
                    "duration_ms": round(duration_ms, 2),
                    "error": str(exc)
                },
                exc_info=True
            )
            
            raise


class StructuredLogger:
    """Structured logger with consistent formatting."""
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
    
    def _add_context(self, extra: dict | None = None) -> dict:
        """Add common context to log entries."""
        context = {
            "environment": settings.environment.value,
            "app_name": settings.app_name,
            "app_version": settings.app_version
        }
        
        if extra:
            context.update(extra)
        
        return context
    
    def info(self, message: str, **kwargs):
        """Log info message."""
        self.logger.info(message, extra=self._add_context(kwargs))
    
    def warning(self, message: str, **kwargs):
        """Log warning message."""
        self.logger.warning(message, extra=self._add_context(kwargs))
    
    def error(self, message: str, exc_info: bool = True, **kwargs):
        """Log error message."""
        self.logger.error(
            message,
            extra=self._add_context(kwargs),
            exc_info=exc_info
        )
    
    def debug(self, message: str, **kwargs):
        """Log debug message."""
        self.logger.debug(message, extra=self._add_context(kwargs))


def get_logger(name: str) -> StructuredLogger:
    """
    Get structured logger instance.
    
    Args:
        name: Logger name (typically __name__)
        
    Returns:
        StructuredLogger instance
    """
    return StructuredLogger(name)
