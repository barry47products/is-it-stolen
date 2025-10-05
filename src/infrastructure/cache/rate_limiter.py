"""Rate limiting implementation using Redis."""

from datetime import timedelta
from typing import Any


class RateLimitExceeded(Exception):
    """Exception raised when rate limit is exceeded."""

    def __init__(self, message: str, retry_after: int = 60) -> None:
        """Initialize rate limit exception.

        Args:
            message: Error message
            retry_after: Seconds until retry is allowed
        """
        super().__init__(message)
        self.retry_after = retry_after


class RateLimiter:
    """Rate limiter using Redis for distributed rate limiting."""

    def __init__(
        self,
        redis_client: Any,
        max_requests: int,
        window: timedelta,
    ) -> None:
        """Initialize rate limiter.

        Args:
            redis_client: Redis client instance
            max_requests: Maximum requests allowed in window
            window: Time window for rate limiting
        """
        self.redis_client = redis_client
        self.max_requests = max_requests
        self.window_seconds = int(window.total_seconds())

    async def check_rate_limit(self, key: str) -> bool:
        """Check if request is within rate limit.

        Args:
            key: Unique key for rate limiting (e.g., phone number, IP)

        Returns:
            True if within limit

        Raises:
            RateLimitExceeded: If rate limit is exceeded
        """
        redis_key = f"rate_limit:{key}"

        # Get current count
        current_count = await self.redis_client.get(redis_key)

        if current_count is None:
            # First request - set counter with expiry
            await self.redis_client.setex(redis_key, self.window_seconds, 1)
            return True

        # Convert bytes to int
        count = int(current_count)

        # Check if limit exceeded
        if count >= self.max_requests:
            # Get TTL for retry_after
            ttl = await self.redis_client.ttl(redis_key)
            retry_after = ttl if ttl > 0 else self.window_seconds

            raise RateLimitExceeded(
                f"Rate limit exceeded for {key}. Retry after {retry_after} seconds.",
                retry_after=retry_after,
            )

        # Increment counter
        await self.redis_client.incr(redis_key)
        return True

    async def reset_rate_limit(self, key: str) -> None:
        """Reset rate limit for a key.

        Args:
            key: Unique key to reset
        """
        redis_key = f"rate_limit:{key}"
        await self.redis_client.delete(redis_key)

    async def get_remaining_requests(self, key: str) -> int:
        """Get remaining requests for a key.

        Args:
            key: Unique key to check

        Returns:
            Number of remaining requests
        """
        redis_key = f"rate_limit:{key}"
        current_count = await self.redis_client.get(redis_key)

        if current_count is None:
            return self.max_requests

        count = int(current_count)
        return max(0, self.max_requests - count)
