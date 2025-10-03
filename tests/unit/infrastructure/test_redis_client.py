"""Unit tests for Redis client."""

from unittest.mock import AsyncMock, patch

import pytest

from src.infrastructure.cache.redis_client import RedisClient, RedisError


class TestRedisClient:
    """Test Redis client operations."""

    @pytest.fixture
    def redis_url(self) -> str:
        """Provide test Redis URL."""
        return "redis://localhost:6379/0"

    @pytest.fixture
    def client(self, redis_url: str) -> RedisClient:
        """Create Redis client for testing."""
        return RedisClient(redis_url)

    async def test_sets_value_with_expiry(self, client: RedisClient) -> None:
        """Should set value with TTL."""
        # Arrange
        mock_redis = AsyncMock()

        with patch("redis.asyncio.from_url", new_callable=AsyncMock) as mock_from_url:
            mock_from_url.return_value = mock_redis

            # Act
            await client.set("test_key", "test_value", ttl=300)

            # Assert
            mock_redis.set.assert_called_once_with("test_key", "test_value", ex=300)

    async def test_gets_existing_value(self, client: RedisClient) -> None:
        """Should get value for existing key."""
        # Arrange
        mock_redis = AsyncMock()
        mock_redis.get.return_value = "test_value"

        with patch("redis.asyncio.from_url", new_callable=AsyncMock) as mock_from_url:
            mock_from_url.return_value = mock_redis

            # Act
            value = await client.get("test_key")

            # Assert
            assert value == "test_value"
            mock_redis.get.assert_called_once_with("test_key")

    async def test_returns_none_for_missing_key(self, client: RedisClient) -> None:
        """Should return None for non-existent key."""
        # Arrange
        mock_redis = AsyncMock()
        mock_redis.get.return_value = None

        with patch("redis.asyncio.from_url", new_callable=AsyncMock) as mock_from_url:
            mock_from_url.return_value = mock_redis

            # Act
            value = await client.get("missing_key")

            # Assert
            assert value is None

    async def test_deletes_key(self, client: RedisClient) -> None:
        """Should delete key."""
        # Arrange
        mock_redis = AsyncMock()
        mock_redis.delete.return_value = 1

        with patch("redis.asyncio.from_url", new_callable=AsyncMock) as mock_from_url:
            mock_from_url.return_value = mock_redis

            # Act
            deleted = await client.delete("test_key")

            # Assert
            assert deleted is True
            mock_redis.delete.assert_called_once_with("test_key")

    async def test_delete_returns_false_for_missing_key(
        self, client: RedisClient
    ) -> None:
        """Should return False when deleting non-existent key."""
        # Arrange
        mock_redis = AsyncMock()
        mock_redis.delete.return_value = 0

        with patch("redis.asyncio.from_url", new_callable=AsyncMock) as mock_from_url:
            mock_from_url.return_value = mock_redis

            # Act
            deleted = await client.delete("missing_key")

            # Assert
            assert deleted is False

    async def test_sets_expiry_on_existing_key(self, client: RedisClient) -> None:
        """Should set TTL on existing key."""
        # Arrange
        mock_redis = AsyncMock()
        mock_redis.expire.return_value = True

        with patch("redis.asyncio.from_url", new_callable=AsyncMock) as mock_from_url:
            mock_from_url.return_value = mock_redis

            # Act
            result = await client.expire("test_key", 600)

            # Assert
            assert result is True
            mock_redis.expire.assert_called_once_with("test_key", 600)

    async def test_expire_returns_false_for_missing_key(
        self, client: RedisClient
    ) -> None:
        """Should return False when setting TTL on non-existent key."""
        # Arrange
        mock_redis = AsyncMock()
        mock_redis.expire.return_value = False

        with patch("redis.asyncio.from_url", new_callable=AsyncMock) as mock_from_url:
            mock_from_url.return_value = mock_redis

            # Act
            result = await client.expire("missing_key", 600)

            # Assert
            assert result is False

    async def test_checks_key_exists(self, client: RedisClient) -> None:
        """Should check if key exists."""
        # Arrange
        mock_redis = AsyncMock()
        mock_redis.exists.return_value = 1

        with patch("redis.asyncio.from_url", new_callable=AsyncMock) as mock_from_url:
            mock_from_url.return_value = mock_redis

            # Act
            exists = await client.exists("test_key")

            # Assert
            assert exists is True
            mock_redis.exists.assert_called_once_with("test_key")

    async def test_exists_returns_false_for_missing_key(
        self, client: RedisClient
    ) -> None:
        """Should return False for non-existent key."""
        # Arrange
        mock_redis = AsyncMock()
        mock_redis.exists.return_value = 0

        with patch("redis.asyncio.from_url", new_callable=AsyncMock) as mock_from_url:
            mock_from_url.return_value = mock_redis

            # Act
            exists = await client.exists("missing_key")

            # Assert
            assert exists is False

    async def test_closes_connection(self, client: RedisClient) -> None:
        """Should close Redis connection."""
        # Arrange
        mock_redis = AsyncMock()

        with patch("redis.asyncio.from_url", new_callable=AsyncMock) as mock_from_url:
            mock_from_url.return_value = mock_redis

            # Act - First establish connection, then close it
            await client.set("test_key", "test_value")
            await client.close()

            # Assert
            mock_redis.close.assert_called_once()

    async def test_raises_redis_error_on_get_failure(self, client: RedisClient) -> None:
        """Should raise RedisError when get operation fails."""
        # Arrange
        mock_redis = AsyncMock()
        mock_redis.get.side_effect = Exception("Connection failed")

        with patch("redis.asyncio.from_url", new_callable=AsyncMock) as mock_from_url:
            mock_from_url.return_value = mock_redis

            # Act & Assert
            with pytest.raises(RedisError) as exc_info:
                await client.get("test_key")

            assert "Failed to get key" in str(exc_info.value)
            assert "Connection failed" in str(exc_info.value)

    async def test_raises_redis_error_on_set_failure(self, client: RedisClient) -> None:
        """Should raise RedisError when set operation fails."""
        # Arrange
        mock_redis = AsyncMock()
        mock_redis.set.side_effect = Exception("Write failed")

        with patch("redis.asyncio.from_url", new_callable=AsyncMock) as mock_from_url:
            mock_from_url.return_value = mock_redis

            # Act & Assert
            with pytest.raises(RedisError) as exc_info:
                await client.set("test_key", "test_value")

            assert "Failed to set key" in str(exc_info.value)

    async def test_raises_redis_error_on_delete_failure(
        self, client: RedisClient
    ) -> None:
        """Should raise RedisError when delete operation fails."""
        # Arrange
        mock_redis = AsyncMock()
        mock_redis.delete.side_effect = Exception("Delete failed")

        with patch("redis.asyncio.from_url", new_callable=AsyncMock) as mock_from_url:
            mock_from_url.return_value = mock_redis

            # Act & Assert
            with pytest.raises(RedisError) as exc_info:
                await client.delete("test_key")

            assert "Failed to delete key" in str(exc_info.value)

    async def test_raises_redis_error_on_expire_failure(
        self, client: RedisClient
    ) -> None:
        """Should raise RedisError when expire operation fails."""
        # Arrange
        mock_redis = AsyncMock()
        mock_redis.expire.side_effect = Exception("Expire failed")

        with patch("redis.asyncio.from_url", new_callable=AsyncMock) as mock_from_url:
            mock_from_url.return_value = mock_redis

            # Act & Assert
            with pytest.raises(RedisError) as exc_info:
                await client.expire("test_key", 300)

            assert "Failed to set expiry" in str(exc_info.value)

    async def test_raises_redis_error_on_exists_failure(
        self, client: RedisClient
    ) -> None:
        """Should raise RedisError when exists operation fails."""
        # Arrange
        mock_redis = AsyncMock()
        mock_redis.exists.side_effect = Exception("Exists check failed")

        with patch("redis.asyncio.from_url", new_callable=AsyncMock) as mock_from_url:
            mock_from_url.return_value = mock_redis

            # Act & Assert
            with pytest.raises(RedisError) as exc_info:
                await client.exists("test_key")

            assert "Failed to check existence" in str(exc_info.value)

    async def test_raises_redis_error_on_close_failure(
        self, client: RedisClient
    ) -> None:
        """Should raise RedisError when closing connection fails."""
        # Arrange
        mock_redis = AsyncMock()
        mock_redis.close.side_effect = Exception("Close failed")

        with patch("redis.asyncio.from_url", new_callable=AsyncMock) as mock_from_url:
            mock_from_url.return_value = mock_redis

            # Act - First establish connection
            await client.set("test_key", "test_value")

            # Assert - Close should raise RedisError
            with pytest.raises(RedisError) as exc_info:
                await client.close()

            assert "Failed to close connection" in str(exc_info.value)

    async def test_close_does_nothing_when_no_connection(
        self, client: RedisClient
    ) -> None:
        """Should not raise error when closing with no connection."""
        # Act & Assert - Should complete without error
        await client.close()

    async def test_reuses_existing_connection(self, client: RedisClient) -> None:
        """Should reuse existing Redis connection instead of creating new one."""
        # Arrange
        mock_redis = AsyncMock()
        mock_redis.delete.return_value = 1

        with patch("redis.asyncio.from_url", new_callable=AsyncMock) as mock_from_url:
            mock_from_url.return_value = mock_redis

            # Act - Call multiple operations
            await client.set("key1", "value1")
            await client.get("key2")
            await client.delete("key3")

            # Assert - Connection should be created only once
            mock_from_url.assert_called_once()
