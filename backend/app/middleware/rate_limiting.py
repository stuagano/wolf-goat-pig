"""
Rate limiting middleware for API endpoints.

Prevents excessive calls to expensive operations like Google Sheets sync.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Optional

from fastapi import HTTPException

logger = logging.getLogger("app.rate_limiting")


class RateLimiter:
    """
    Simple in-memory rate limiter.

    For production, consider using Redis for distributed rate limiting.
    """

    def __init__(self):
        self.last_request: Dict[str, datetime] = {}
        self.request_counts: Dict[str, int] = {}

    def check_limit(
        self,
        key: str,
        min_interval_seconds: int = 3600,  # 1 hour default
        client_id: Optional[str] = None
    ) -> bool:
        """
        Check if a request should be allowed based on rate limit.

        Args:
            key: Identifier for the rate-limited operation
            min_interval_seconds: Minimum seconds between requests
            client_id: Optional client identifier for per-client limits

        Returns:
            True if request is allowed

        Raises:
            HTTPException: 429 if rate limit exceeded
        """
        rate_key = f"{key}:{client_id or 'system'}"
        now = datetime.now()
        min_interval = timedelta(seconds=min_interval_seconds)

        if rate_key in self.last_request:
            time_since_last = now - self.last_request[rate_key]

            if time_since_last < min_interval:
                remaining = min_interval - time_since_last
                remaining_seconds = int(remaining.total_seconds())

                logger.warning(
                    f"Rate limit exceeded for {key} "
                    f"(client: {client_id or 'system'}). "
                    f"Retry after {remaining_seconds}s"
                )

                raise HTTPException(
                    status_code=429,
                    detail={
                        "error": "Too Many Requests",
                        "message": f"Rate limit exceeded. This endpoint can only be called once per {min_interval_seconds // 3600} hour(s).",
                        "retry_after_seconds": remaining_seconds,
                        "last_request": self.last_request[rate_key].isoformat(),
                        "next_allowed": (now + remaining).isoformat()
                    },
                    headers={
                        "Retry-After": str(remaining_seconds),
                        "X-RateLimit-Limit": "1",
                        "X-RateLimit-Remaining": "0",
                        "X-RateLimit-Reset": str(int((now + remaining).timestamp()))
                    }
                )

        # Request allowed
        self.last_request[rate_key] = now
        self.request_counts[rate_key] = self.request_counts.get(rate_key, 0) + 1

        logger.info(
            f"Rate limit check passed for {key} "
            f"(client: {client_id or 'system'}, "
            f"total requests: {self.request_counts[rate_key]})"
        )

        return True

    def reset(self, key: str, client_id: Optional[str] = None) -> None:
        """Reset rate limit for a specific key."""
        rate_key = f"{key}:{client_id or 'system'}"
        if rate_key in self.last_request:
            del self.last_request[rate_key]
        if rate_key in self.request_counts:
            del self.request_counts[rate_key]
        logger.info(f"Rate limit reset for {rate_key}")

    def get_stats(self) -> Dict:
        """Get rate limiting statistics."""
        return {
            "active_keys": len(self.last_request),
            "total_requests": sum(self.request_counts.values()),
            "keys": {
                key: {
                    "last_request": timestamp.isoformat(),
                    "total_requests": self.request_counts.get(key, 0)
                }
                for key, timestamp in self.last_request.items()
            }
        }


# Global rate limiter instance
rate_limiter = RateLimiter()
