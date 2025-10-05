"""Tests for rate limiter."""

from datetime import timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.infrastructure.cache.rate_limiter import RateLimiter, RateLimitExceeded


@pytest.mark.unit
class TestRateLimiter:
    """Test rate limiter."""

    @pytest.mark.asyncio
    async def test_allows_request_within_limit(self) -> None:
        """Test that requests within limit are allowed."""
        # Arrange
        redis_client = MagicMock()
        redis_client.get = AsyncMock(return_value=None)
        redis_client.setex = AsyncMock()

        limiter = RateLimiter(
            redis_client, max_requests=10, window=timedelta(minutes=1)
        )

        # Act
        result = await limiter.check_rate_limit("test_key")

        # Assert
        assert result is True
        redis_client.get.assert_called_once_with("rate_limit:test_key")

    @pytest.mark.asyncio
    async def test_increments_counter_on_request(self) -> None:
        """Test that counter is incremented on each request."""
        # Arrange
        redis_client = MagicMock()
        redis_client.get = AsyncMock(return_value=b"5")
        redis_client.incr = AsyncMock(return_value=6)

        limiter = RateLimiter(
            redis_client, max_requests=10, window=timedelta(minutes=1)
        )

        # Act
        await limiter.check_rate_limit("test_key")

        # Assert
        redis_client.incr.assert_called_once_with("rate_limit:test_key")

    @pytest.mark.asyncio
    async def test_raises_exception_when_limit_exceeded(self) -> None:
        """Test that RateLimitExceeded is raised when limit is exceeded."""
        # Arrange
        redis_client = MagicMock()
        redis_client.get = AsyncMock(return_value=b"10")
        redis_client.ttl = AsyncMock(return_value=60)

        limiter = RateLimiter(
            redis_client, max_requests=10, window=timedelta(minutes=1)
        )

        # Act & Assert
        with pytest.raises(RateLimitExceeded) as exc_info:
            await limiter.check_rate_limit("test_key")

        assert "Rate limit exceeded" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_sets_expiry_on_first_request(self) -> None:
        """Test that expiry is set on first request."""
        # Arrange
        redis_client = MagicMock()
        redis_client.get = AsyncMock(return_value=None)
        redis_client.setex = AsyncMock()

        limiter = RateLimiter(
            redis_client, max_requests=10, window=timedelta(minutes=1)
        )

        # Act
        await limiter.check_rate_limit("test_key")

        # Assert
        redis_client.setex.assert_called_once_with("rate_limit:test_key", 60, 1)

    @pytest.mark.asyncio
    async def test_different_keys_have_separate_limits(self) -> None:
        """Test that different keys have separate rate limits."""
        # Arrange
        redis_client = MagicMock()
        redis_client.get = AsyncMock(return_value=None)
        redis_client.setex = AsyncMock()

        limiter = RateLimiter(
            redis_client, max_requests=10, window=timedelta(minutes=1)
        )

        # Act
        await limiter.check_rate_limit("key1")
        await limiter.check_rate_limit("key2")

        # Assert
        assert redis_client.get.call_count == 2
        assert redis_client.setex.call_count == 2

    @pytest.mark.asyncio
    async def test_returns_retry_after_seconds_when_limited(self) -> None:
        """Test that retry_after is included in exception."""
        # Arrange
        redis_client = MagicMock()
        redis_client.get = AsyncMock(return_value=b"15")
        redis_client.ttl = AsyncMock(return_value=45)

        limiter = RateLimiter(
            redis_client, max_requests=10, window=timedelta(minutes=1)
        )

        # Act & Assert
        with pytest.raises(RateLimitExceeded) as exc_info:
            await limiter.check_rate_limit("test_key")

        assert exc_info.value.retry_after == 45

    @pytest.mark.asyncio
    async def test_configurable_max_requests(self) -> None:
        """Test that max_requests is configurable."""
        # Arrange
        redis_client = MagicMock()
        redis_client.get = AsyncMock(return_value=b"5")
        redis_client.ttl = AsyncMock(return_value=60)

        limiter = RateLimiter(redis_client, max_requests=5, window=timedelta(minutes=1))

        # Act & Assert
        with pytest.raises(RateLimitExceeded):
            await limiter.check_rate_limit("test_key")

    @pytest.mark.asyncio
    async def test_configurable_window(self) -> None:
        """Test that time window is configurable."""
        # Arrange
        redis_client = MagicMock()
        redis_client.get = AsyncMock(return_value=None)
        redis_client.setex = AsyncMock()

        limiter = RateLimiter(
            redis_client, max_requests=10, window=timedelta(seconds=30)
        )

        # Act
        await limiter.check_rate_limit("test_key")

        # Assert
        redis_client.setex.assert_called_once_with("rate_limit:test_key", 30, 1)

    @pytest.mark.asyncio
    async def test_reset_rate_limit(self) -> None:
        """Test that rate limit can be reset."""
        # Arrange
        redis_client = MagicMock()
        redis_client.delete = AsyncMock()

        limiter = RateLimiter(
            redis_client, max_requests=10, window=timedelta(minutes=1)
        )

        # Act
        await limiter.reset_rate_limit("test_key")

        # Assert
        redis_client.delete.assert_called_once_with("rate_limit:test_key")

    @pytest.mark.asyncio
    async def test_get_remaining_requests(self) -> None:
        """Test getting remaining requests."""
        # Arrange
        redis_client = MagicMock()
        redis_client.get = AsyncMock(return_value=b"7")

        limiter = RateLimiter(
            redis_client, max_requests=10, window=timedelta(minutes=1)
        )

        # Act
        remaining = await limiter.get_remaining_requests("test_key")

        # Assert
        assert remaining == 3

    @pytest.mark.asyncio
    async def test_get_remaining_requests_when_no_limit(self) -> None:
        """Test getting remaining requests when no limit set."""
        # Arrange
        redis_client = MagicMock()
        redis_client.get = AsyncMock(return_value=None)

        limiter = RateLimiter(
            redis_client, max_requests=10, window=timedelta(minutes=1)
        )

        # Act
        remaining = await limiter.get_remaining_requests("test_key")

        # Assert
        assert remaining == 10
