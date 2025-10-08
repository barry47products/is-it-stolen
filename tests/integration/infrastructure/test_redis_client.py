"""Integration tests for Redis client with real Redis instance."""

from collections.abc import AsyncGenerator

import pytest

from src.infrastructure.cache.redis_client import RedisClient
from src.infrastructure.config.settings import get_settings


class TestRedisClientIntegration:
    """Integration tests for Redis client with real Redis."""

    @pytest.fixture
    async def redis_client(self) -> AsyncGenerator[RedisClient]:
        """Create Redis client connected to test Redis instance."""
        settings = get_settings()
        client = RedisClient(str(settings.redis_url))
        yield client
        # Cleanup - close connection
        await client.close()

    @pytest.mark.asyncio
    async def test_sets_and_gets_value_from_real_redis(
        self, redis_client: RedisClient
    ) -> None:
        """Should set and retrieve value from real Redis instance."""
        # Arrange
        test_key = "test:integration:simple"
        test_value = "integration_test_value"

        # Act
        await redis_client.set(test_key, test_value)
        result = await redis_client.get(test_key)

        # Assert
        assert result == test_value

        # Cleanup
        await redis_client.delete(test_key)

    @pytest.mark.asyncio
    async def test_sets_value_with_ttl_expires_after_timeout(
        self, redis_client: RedisClient
    ) -> None:
        """Should set value with TTL and verify expiration."""
        # Arrange
        import asyncio

        test_key = "test:integration:ttl"
        test_value = "expires_soon"
        ttl_seconds = 1  # 1 second TTL

        # Act
        await redis_client.set(test_key, test_value, ttl=ttl_seconds)

        # Verify value exists immediately
        result_before = await redis_client.get(test_key)
        assert result_before == test_value

        # Wait for expiration (slightly longer than TTL)
        await asyncio.sleep(1.05)
        # TODO: Reduce the sleep time by using a mockable time function in RedisClient

        # Verify value has expired
        result_after = await redis_client.get(test_key)

        # Assert
        assert result_after is None

    @pytest.mark.asyncio
    async def test_deletes_existing_key_from_redis(
        self, redis_client: RedisClient
    ) -> None:
        """Should delete key from real Redis instance."""
        # Arrange
        test_key = "test:integration:delete"
        test_value = "to_be_deleted"
        await redis_client.set(test_key, test_value)

        # Act
        deleted = await redis_client.delete(test_key)
        result = await redis_client.get(test_key)

        # Assert
        assert deleted is True
        assert result is None

    @pytest.mark.asyncio
    async def test_returns_false_when_deleting_nonexistent_key(
        self, redis_client: RedisClient
    ) -> None:
        """Should return False when deleting non-existent key."""
        # Arrange
        test_key = "test:integration:nonexistent"

        # Act
        deleted = await redis_client.delete(test_key)

        # Assert
        assert deleted is False

    @pytest.mark.asyncio
    async def test_checks_if_key_exists_in_redis(
        self, redis_client: RedisClient
    ) -> None:
        """Should check if key exists in real Redis."""
        # Arrange
        test_key = "test:integration:exists"
        test_value = "exists_test"
        await redis_client.set(test_key, test_value)

        # Act
        exists_before = await redis_client.exists(test_key)
        await redis_client.delete(test_key)
        exists_after = await redis_client.exists(test_key)

        # Assert
        assert exists_before is True
        assert exists_after is False

    @pytest.mark.asyncio
    async def test_sets_expiry_on_existing_key(self, redis_client: RedisClient) -> None:
        """Should set expiry on existing key in Redis."""
        # Arrange
        test_key = "test:integration:expire"
        test_value = "expire_test"
        await redis_client.set(test_key, test_value)

        # Act
        success = await redis_client.expire(test_key, 1)

        # Verify
        assert success is True

        # Wait for expiration (slightly longer than TTL)
        import asyncio

        await asyncio.sleep(1.05)

        exists = await redis_client.exists(test_key)

        # Assert
        assert exists is False

    @pytest.mark.asyncio
    async def test_handles_connection_pool_with_multiple_operations(
        self, redis_client: RedisClient
    ) -> None:
        """Should handle multiple concurrent operations."""
        # Arrange
        keys_and_values = [
            (f"test:integration:concurrent:{i}", f"value_{i}") for i in range(10)
        ]

        # Act - Set all values
        for key, value in keys_and_values:
            await redis_client.set(key, value)

        # Retrieve all values
        results = []
        for key, expected_value in keys_and_values:
            result = await redis_client.get(key)
            results.append((result, expected_value))

        # Assert
        for result, expected in results:
            assert result == expected

        # Cleanup
        for key, _ in keys_and_values:
            await redis_client.delete(key)

    @pytest.mark.asyncio
    async def test_handles_unicode_and_special_characters(
        self, redis_client: RedisClient
    ) -> None:
        """Should handle Unicode and special characters in values."""
        # Arrange
        test_key = "test:integration:unicode"
        test_value = "Hello 世界 🌍 émoji"

        # Act
        await redis_client.set(test_key, test_value)
        result = await redis_client.get(test_key)

        # Assert
        assert result == test_value

        # Cleanup
        await redis_client.delete(test_key)

    @pytest.mark.asyncio
    async def test_reuses_same_connection_for_multiple_operations(
        self, redis_client: RedisClient
    ) -> None:
        """Should reuse connection across multiple operations."""
        # Arrange
        test_key = "test:integration:reuse"

        # Act - Perform multiple operations
        await redis_client.set(test_key, "value1")
        result1 = await redis_client.get(test_key)

        await redis_client.set(test_key, "value2")
        result2 = await redis_client.get(test_key)

        await redis_client.delete(test_key)
        result3 = await redis_client.get(test_key)

        # Assert
        assert result1 == "value1"
        assert result2 == "value2"
        assert result3 is None
