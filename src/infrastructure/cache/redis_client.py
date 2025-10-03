"""Redis client for caching and session management."""

import redis.asyncio as redis


class RedisError(Exception):
    """Exception raised for Redis-related errors."""

    pass


class RedisClient:
    """Async Redis client with connection pooling."""

    def __init__(self, redis_url: str) -> None:
        """Initialize Redis client.

        Args:
            redis_url: Redis connection URL (e.g., redis://localhost:6379/0)
        """
        self.redis_url = redis_url
        self._redis: redis.Redis | None = None

    async def _get_redis(self) -> redis.Redis:
        """Get Redis connection.

        Returns:
            Redis connection instance

        Note:
            Connection is created lazily on first use
        """
        if self._redis is None:
            self._redis = await redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True,
            )
        return self._redis

    async def set(
        self,
        key: str,
        value: str,
        ttl: int | None = None,
    ) -> None:
        """Set value with optional TTL.

        Args:
            key: Redis key
            value: Value to store
            ttl: Time to live in seconds (optional)

        Raises:
            RedisError: If Redis operation fails
        """
        try:
            client = await self._get_redis()
            await client.set(key, value, ex=ttl)
        except Exception as e:
            raise RedisError(f"Failed to set key: {e}") from e

    async def get(self, key: str) -> str | None:
        """Get value by key.

        Args:
            key: Redis key

        Returns:
            Value if exists, None otherwise

        Raises:
            RedisError: If Redis operation fails
        """
        try:
            client = await self._get_redis()
            value: str | None = await client.get(key)
            return value
        except Exception as e:
            raise RedisError(f"Failed to get key: {e}") from e

    async def delete(self, key: str) -> bool:
        """Delete key.

        Args:
            key: Redis key to delete

        Returns:
            True if key was deleted, False if key didn't exist

        Raises:
            RedisError: If Redis operation fails
        """
        try:
            client = await self._get_redis()
            result: int = await client.delete(key)
            return result > 0
        except Exception as e:
            raise RedisError(f"Failed to delete key: {e}") from e

    async def expire(self, key: str, ttl: int) -> bool:
        """Set TTL on existing key.

        Args:
            key: Redis key
            ttl: Time to live in seconds

        Returns:
            True if TTL was set, False if key doesn't exist

        Raises:
            RedisError: If Redis operation fails
        """
        try:
            client = await self._get_redis()
            result: bool = await client.expire(key, ttl)
            return result
        except Exception as e:
            raise RedisError(f"Failed to set expiry: {e}") from e

    async def exists(self, key: str) -> bool:
        """Check if key exists.

        Args:
            key: Redis key

        Returns:
            True if key exists, False otherwise

        Raises:
            RedisError: If Redis operation fails
        """
        try:
            client = await self._get_redis()
            result: int = await client.exists(key)
            return result > 0
        except Exception as e:
            raise RedisError(f"Failed to check existence: {e}") from e

    async def close(self) -> None:
        """Close Redis connection.

        Raises:
            RedisError: If closing connection fails
        """
        try:
            if self._redis is not None:
                await self._redis.aclose()  # type: ignore[attr-defined]
                self._redis = None
        except Exception as e:
            raise RedisError(f"Failed to close connection: {e}") from e
