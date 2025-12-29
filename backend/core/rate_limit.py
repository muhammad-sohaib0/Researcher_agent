"""
Rate Limiting Module

Implements token bucket algorithm for per-user rate limiting.
Provides API endpoint protection with configurable limits.
"""

import time
import logging
from typing import Dict, Optional, Tuple
from dataclasses import dataclass, field
from functools import wraps
from collections import defaultdict

from fastapi import Request, HTTPException, Depends
from fastapi.responses import JSONResponse

from ..core.config import get_settings

logger = logging.getLogger(__name__)


@dataclass
class TokenBucket:
    """
    Token bucket implementation for rate limiting.

    Attributes:
        capacity: Maximum number of tokens in the bucket
        tokens: Current number of tokens available
        last_update: Timestamp of last token refill
        rate: Tokens added per second
    """
    capacity: float
    tokens: float
    last_update: float
    rate: float = 1.0

    def __init__(self, capacity: float, rate: float = 1.0):
        self.capacity = capacity
        self.tokens = capacity
        self.last_update = time.time()
        self.rate = rate

    def consume(self, tokens: float = 1) -> bool:
        """
        Try to consume tokens from the bucket.

        Args:
            tokens: Number of tokens to consume

        Returns:
            True if tokens were consumed, False if rate limited
        """
        self._refill()

        if self.tokens >= tokens:
            self.tokens -= tokens
            return True

        return False

    def _refill(self) -> None:
        """Refill tokens based on elapsed time."""
        now = time.time()
        elapsed = now - self.last_update
        self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)
        self.last_update = now

    @property
    def remaining(self) -> float:
        """Get remaining tokens."""
        self._refill()
        return self.tokens

    @property
    def is_exhausted(self) -> bool:
        """Check if bucket is empty."""
        self._refill()
        return self.tokens < 1


class RateLimiter:
    """
    Rate limiter with per-user and endpoint tracking.

    Supports different rate limits for different endpoints.
    """

    def __init__(self):
        self._buckets: Dict[str, Dict[str, TokenBucket]] = defaultdict(dict)
        self._user_buckets: Dict[str, TokenBucket] = {}
        self._default_rate = 100  # requests per window
        self._default_window = 60  # seconds

    def _get_bucket(self, identifier: str, endpoint: str, capacity: int, rate: float) -> TokenBucket:
        """Get or create a token bucket for an identifier and endpoint."""
        key = f"{identifier}:{endpoint}"

        if key not in self._buckets[identifier]:
            self._buckets[identifier][key] = TokenBucket(capacity=capacity, rate=rate)

        return self._buckets[identifier][key]

    def check_rate_limit(
        self,
        identifier: str,
        endpoint: str = "default",
        capacity: Optional[int] = None,
        rate: Optional[float] = None
    ) -> Tuple[bool, float, float]:
        """
        Check if request is within rate limit.

        Args:
            identifier: User/API key identifier
            endpoint: API endpoint path
            capacity: Maximum tokens (defaults to config)
            rate: Tokens per second (defaults to capacity/window)

        Returns:
            Tuple of (allowed, remaining_tokens, reset_time_seconds)
        """
        settings = get_settings()

        if capacity is None:
            capacity = settings.rate_limit_requests
        if rate is None:
            rate = capacity / settings.rate_limit_window_seconds

        bucket = self._get_bucket(identifier, endpoint, capacity, rate)

        allowed = bucket.consume(1)

        if allowed:
            return True, bucket.remaining, 0
        else:
            # Calculate time until next token
            wait_time = (1 - bucket.remaining) / bucket.rate
            return False, 0, wait_time

    def get_user_bucket(self, user_id: int, capacity: int = 100) -> TokenBucket:
        """Get or create a user-specific rate limit bucket."""
        identifier = f"user_{user_id}"

        if identifier not in self._user_buckets:
            self._user_buckets[identifier] = TokenBucket(capacity=capacity)

        return self._user_buckets[identifier]

    def reset(self, identifier: Optional[str] = None) -> None:
        """Reset rate limits for an identifier or all."""
        if identifier:
            self._buckets.pop(identifier, None)
            self._user_buckets.pop(f"user_{identifier}", None)
        else:
            self._buckets.clear()
            self._user_buckets.clear()

    def get_stats(self, identifier: str) -> Dict:
        """Get rate limit stats for an identifier."""
        user_bucket = self._user_buckets.get(f"user_{identifier}")
        endpoint_buckets = {
            key.split(":")[1]: {
                "remaining": bucket.remaining,
                "capacity": bucket.capacity
            }
            for key, bucket in self._buckets.get(identifier, {}).items()
        }

        return {
            "user_bucket": {
                "remaining": user_bucket.remaining if user_bucket else 0,
                "capacity": user_bucket.capacity if user_bucket else 0
            },
            "endpoints": endpoint_buckets
        }


# Global rate limiter instance
_rate_limiter: Optional[RateLimiter] = None


def get_rate_limiter() -> RateLimiter:
    """Get global rate limiter instance."""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter()
    return _rate_limiter


# Rate limit configuration for different endpoints
ENDPOINT_LIMITS = {
    "/api/auth/login": {"capacity": 10, "window": 60},  # 10 login attempts per minute
    "/api/auth/signup": {"capacity": 5, "window": 300},  # 5 signups per 5 minutes
    "/api/chat/message": {"capacity": 30, "window": 60},  # 30 messages per minute
    "/api/files/upload": {"capacity": 20, "window": 300},  # 20 uploads per 5 minutes
    "/api/search": {"capacity": 60, "window": 60},  # 60 searches per minute
}


async def rate_limit_middleware(request: Request, call_next):
    """
    FastAPI middleware for rate limiting.

    Add this to your main.py:
        app.add_middleware(rate_limit_middleware)
    """
    rate_limiter = get_rate_limiter()

    # Get client identifier
    client_ip = request.client.host if request.client else "unknown"
    auth_header = request.headers.get("Authorization")

    if auth_header:
        # Use user ID from token if available
        identifier = auth_header[:20]  # Truncated for privacy
    else:
        identifier = f"ip_{client_ip}"

    # Get endpoint-specific limits
    path = request.url.path
    limits = ENDPOINT_LIMITS.get(path, {})

    allowed, remaining, wait_time = rate_limiter.check_rate_limit(
        identifier=identifier,
        endpoint=path,
        capacity=limits.get("capacity"),
        rate=limits.get("rate")
    )

    # Add rate limit headers
    response = await call_next(request)

    if remaining >= 0:
        response.headers["X-RateLimit-Remaining"] = str(int(remaining))
        response.headers["X-RateLimit-Limit"] = str(limits.get("capacity", 100))

    if not allowed:
        response = JSONResponse(
            status_code=429,
            content={
                "error": "Rate limit exceeded",
                "message": f"Too many requests. Please wait {int(wait_time)} seconds.",
                "retry_after": int(wait_time)
            }
        )
        response.headers["Retry-After"] = str(int(wait_time))

    return response


def rate_limit_dependency(
    capacity: int = None,
    window: int = None,
    key_func: callable = None
):
    """
    Dependency for rate limiting endpoints.

    Usage:
        @router.post("/endpoint")
        async def endpoint(
            current_user: User = Depends(get_current_user),
            _=Depends(rate_limit_dependency(capacity=10, window=60))
        ):
            ...

    Args:
        capacity: Maximum requests per window
        window: Time window in seconds
        key_func: Custom function to extract rate limit key from request
    """
    async def rate_limit(
        request: Request,
        current_user = None
    ):
        rate_limiter = get_rate_limiter()

        # Determine identifier
        if key_func:
            identifier = key_func(request)
        elif current_user:
            identifier = f"user_{current_user.id}"
        else:
            client_ip = request.client.host if request.client else "unknown"
            identifier = f"ip_{client_ip}"

        # Calculate rate
        rate = (capacity or 100) / (window or 60)

        allowed, remaining, wait_time = rate_limiter.check_rate_limit(
            identifier=identifier,
            endpoint=request.url.path,
            capacity=capacity,
            rate=rate
        )

        if not allowed:
            raise HTTPException(
                status_code=429,
                detail={
                    "error": "Rate limit exceeded",
                    "message": f"Too many requests. Please wait {int(wait_time)} seconds.",
                    "retry_after": int(wait_time)
                }
            )

        return remaining

    return rate_limit


class UserRateLimit:
    """
    Per-user rate limiter using FastAPI Depends.

    Usage:
        @router.post("/message")
        async def send_message(
            message: MessageCreate,
            current_user: User = Depends(get_current_user),
            rate_limit: UserRateLimit = Depends(UserRateLimit(30, 60))  # 30 per minute
        ):
            ...
    """

    def __init__(self, capacity: int, window: int, per_user: bool = True):
        self.capacity = capacity
        self.window = window
        self.per_user = per_user

    async def __call__(
        self,
        request: Request,
        current_user = None
    ):
        if not self.per_user:
            return True

        rate_limiter = get_rate_limiter()

        if current_user:
            bucket = rate_limiter.get_user_bucket(current_user.id, self.capacity)
            allowed = bucket.consume(1)

            if not allowed:
                wait_time = (1 - bucket.remaining) / (self.capacity / self.window)
                raise HTTPException(
                    status_code=429,
                    detail={
                        "error": "Rate limit exceeded",
                        "message": f"Too many requests. Please wait {int(wait_time)} seconds.",
                        "retry_after": int(wait_time)
                    }
                )

        return True
