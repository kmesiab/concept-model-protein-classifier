"""
Rate limiting functionality using Redis for distributed rate limiting.
"""

import logging
import os
import time
from datetime import datetime, timezone
from typing import Optional, Tuple

import redis

logger = logging.getLogger(__name__)


class RateLimiter:
    """
    Token bucket rate limiter using Redis.

    Supports both per-minute and daily limits.
    """

    def __init__(self, redis_url: str = None):
        """
        Initialize rate limiter.

        Args:
            redis_url: Redis connection URL (defaults to REDIS_URL env var or localhost)
        """
        if redis_url is None:
            redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")

        try:
            self.redis_client = redis.from_url(redis_url, decode_responses=True)
            self.redis_client.ping()
            self.redis_available = True
        except (redis.ConnectionError, redis.RedisError) as e:
            logger.warning("Redis not available: %s", e)
            logger.warning(
                "Rate limiting will use in-memory fallback (not suitable for production)"
            )
            self.redis_available = False
            self._memory_store: dict = {}  # type: ignore  # Fallback for development

    def check_rate_limit(
        self,
        api_key_hash: str,
        max_requests_per_minute: int,
        max_sequences_per_day: int,
        num_sequences: int = 1,
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if request is within rate limits.

        Args:
            api_key_hash: Hashed API key identifier
            max_requests_per_minute: Maximum requests per minute
            max_sequences_per_day: Maximum sequences per day
            num_sequences: Number of sequences in this request

        Returns:
            Tuple of (is_allowed, error_message)
        """
        # Check per-minute rate limit
        minute_key = f"rate_limit:minute:{api_key_hash}:{self._get_current_minute()}"
        minute_allowed, minute_error = self._check_counter(
            minute_key, max_requests_per_minute, 60, "requests per minute"  # TTL in seconds
        )

        if not minute_allowed:
            return False, minute_error

        # Check daily sequence limit
        day_key = f"rate_limit:day:{api_key_hash}:{self._get_current_day()}"
        daily_allowed, daily_error = self._check_counter(
            day_key,
            max_sequences_per_day,  # Fixed: check against the limit directly
            86400,  # 24 hours in seconds
            "sequences per day",
            increment=num_sequences,
        )

        if not daily_allowed:
            return False, daily_error

        return True, None

    def _check_counter(
        self, key: str, limit: int, ttl: int, limit_type: str, increment: int = 1
    ) -> Tuple[bool, Optional[str]]:
        """
        Check and increment a counter with limit.

        Args:
            key: Redis key
            limit: Maximum allowed value
            ttl: Time to live in seconds
            limit_type: Description for error message
            increment: Amount to increment

        Returns:
            Tuple of (is_allowed, error_message)
        """
        if self.redis_available:
            try:
                current = self.redis_client.get(key)
                current_value = int(current) if current else 0

                # Check if adding this increment would exceed the limit
                if current_value + increment > limit:
                    return False, f"Rate limit exceeded: {limit} {limit_type}"

                # Increment counter
                pipe = self.redis_client.pipeline()
                pipe.incr(key, increment)
                pipe.expire(key, ttl)
                pipe.execute()

                return True, None
            except redis.RedisError as e:
                logger.error("Redis error: %s", e)
                # Fallback to allowing request if Redis fails
                return True, None
        else:
            # In-memory fallback (not production-ready)
            current_time = time.time()

            if key not in self._memory_store:
                self._memory_store[key] = {"count": 0, "expires_at": current_time + ttl}

            entry = self._memory_store[key]

            # Reset if expired
            if current_time >= entry["expires_at"]:
                entry["count"] = 0
                entry["expires_at"] = current_time + ttl

            # Check if adding this increment would exceed the limit
            if entry["count"] + increment > limit:
                return False, f"Rate limit exceeded: {limit} {limit_type}"

            entry["count"] += increment
            return True, None

    def _get_current_minute(self) -> str:
        """Get current minute as YYYY-MM-DD-HH-MM."""
        return datetime.now(timezone.utc).strftime("%Y-%m-%d-%H-%M")

    def _get_current_day(self) -> str:
        """Get current day as YYYY-MM-DD."""
        return datetime.now(timezone.utc).strftime("%Y-%m-%d")

    def get_usage(self, api_key_hash: str) -> dict:
        """
        Get current usage statistics for an API key.

        Args:
            api_key_hash: Hashed API key identifier

        Returns:
            Dictionary with usage stats
        """
        minute_key = f"rate_limit:minute:{api_key_hash}:{self._get_current_minute()}"
        day_key = f"rate_limit:day:{api_key_hash}:{self._get_current_day()}"

        if self.redis_available:
            try:
                minute_count = self.redis_client.get(minute_key)
                day_count = self.redis_client.get(day_key)

                return {
                    "requests_this_minute": int(minute_count) if minute_count else 0,
                    "sequences_today": int(day_count) if day_count else 0,
                }
            except redis.RedisError:
                pass
        else:
            minute_entry = self._memory_store.get(minute_key, {})
            day_entry = self._memory_store.get(day_key, {})

            return {
                "requests_this_minute": minute_entry.get("count", 0),
                "sequences_today": day_entry.get("count", 0),
            }

        return {"requests_this_minute": 0, "sequences_today": 0}


# Global rate limiter instance
rate_limiter: Optional[RateLimiter] = None


def get_rate_limiter() -> RateLimiter:
    """Get or create the rate limiter instance."""
    global rate_limiter
    if rate_limiter is None:
        rate_limiter = RateLimiter()
    return rate_limiter
