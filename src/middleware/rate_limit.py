"""
Rate Limiting Middleware

Provides:
- Request rate limiting per IP/user
- Configurable limits
- Rate limit headers
"""

from __future__ import annotations

import time
from collections import defaultdict
from typing import Callable

from fastapi import Request, Response, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware

from src.config.settings import settings


class RateLimiter:
    """Simple in-memory rate limiter."""
    
    def __init__(self, requests_per_minute: int = 60):
        """
        Initialize rate limiter.
        
        Args:
            requests_per_minute: Maximum requests per minute
        """
        self.requests_per_minute = requests_per_minute
        self.requests: dict[str, list[float]] = defaultdict(list)
    
    def is_allowed(self, identifier: str) -> tuple[bool, int]:
        """
        Check if request is allowed.
        
        Args:
            identifier: Client identifier (IP, user ID, etc.)
            
        Returns:
            Tuple of (is_allowed, remaining_requests)
        """
        now = time.time()
        minute_ago = now - 60
        
        # Clean old requests
        self.requests[identifier] = [
            req_time for req_time in self.requests[identifier]
            if req_time > minute_ago
        ]
        
        # Check limit
        current_requests = len(self.requests[identifier])
        
        if current_requests >= self.requests_per_minute:
            return False, 0
        
        # Add new request
        self.requests[identifier].append(now)
        
        return True, self.requests_per_minute - current_requests - 1
    
    def get_reset_time(self, identifier: str) -> int:
        """
        Get time until rate limit resets.
        
        Args:
            identifier: Client identifier
            
        Returns:
            Seconds until reset
        """
        if not self.requests[identifier]:
            return 0
        
        oldest_request = min(self.requests[identifier])
        reset_time = oldest_request + 60
        
        return max(0, int(reset_time - time.time()))


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware for rate limiting requests."""
    
    def __init__(self, app, requests_per_minute: int | None = None):
        """
        Initialize rate limit middleware.
        
        Args:
            app: FastAPI app
            requests_per_minute: Max requests per minute (from settings if None)
        """
        super().__init__(app)
        self.enabled = settings.rate_limit_enabled
        self.limiter = RateLimiter(
            requests_per_minute=requests_per_minute or settings.rate_limit_per_minute
        )
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Check rate limit and process request.
        
        Args:
            request: Incoming request
            call_next: Next middleware/handler
            
        Returns:
            Response
            
        Raises:
            HTTPException: If rate limit exceeded
        """
        if not self.enabled:
            return await call_next(request)
        
        # Exempt health check endpoints
        if request.url.path in ["/health", "/api/health", "/metrics"]:
            return await call_next(request)
        
        # Get client identifier (IP address or user ID)
        identifier = request.client.host if request.client else "unknown"
        
        # Check rate limit
        is_allowed, remaining = self.limiter.is_allowed(identifier)
        
        if not is_allowed:
            reset_time = self.limiter.get_reset_time(identifier)
            
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. Try again in {reset_time} seconds.",
                headers={
                    "X-RateLimit-Limit": str(settings.rate_limit_per_minute),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(reset_time),
                    "Retry-After": str(reset_time)
                }
            )
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(settings.rate_limit_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        
        return response
