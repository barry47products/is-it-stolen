"""Storage for conversation contexts using Redis."""

import json
from typing import Protocol

from redis.asyncio import Redis

from src.presentation.bot.context import ConversationContext

DEFAULT_TTL_SECONDS = 3600  # 1 hour


class ConversationStorage(Protocol):
    """Protocol for conversation storage implementations."""

    async def get(self, phone_number: str) -> ConversationContext | None:
        """Get conversation context for phone number.

        Args:
            phone_number: User's phone number

        Returns:
            ConversationContext if exists, None otherwise
        """
        ...  # pragma: no cover

    async def save(
        self, context: ConversationContext, ttl_seconds: int = DEFAULT_TTL_SECONDS
    ) -> None:
        """Save conversation context.

        Args:
            context: Conversation context to save
            ttl_seconds: Time-to-live in seconds (default 1 hour)
        """
        ...  # pragma: no cover

    async def delete(self, phone_number: str) -> None:
        """Delete conversation context.

        Args:
            phone_number: User's phone number
        """
        ...  # pragma: no cover

    async def exists(self, phone_number: str) -> bool:
        """Check if conversation context exists.

        Args:
            phone_number: User's phone number

        Returns:
            True if context exists, False otherwise
        """
        ...  # pragma: no cover


class RedisConversationStorage:
    """Redis-based conversation storage implementation."""

    def __init__(self, redis_client: Redis) -> None:  # type: ignore[type-arg]
        """Initialize storage with Redis client.

        Args:
            redis_client: Async Redis client
        """
        self.redis = redis_client

    def _get_key(self, phone_number: str) -> str:
        """Generate Redis key for phone number.

        Args:
            phone_number: User's phone number

        Returns:
            Redis key
        """
        return f"conversation:{phone_number}"

    async def get(self, phone_number: str) -> ConversationContext | None:
        """Get conversation context for phone number.

        Args:
            phone_number: User's phone number

        Returns:
            ConversationContext if exists, None otherwise
        """
        key = self._get_key(phone_number)
        data = await self.redis.get(key)

        if data is None:
            return None

        # Deserialize from JSON
        context_dict = json.loads(data)
        return ConversationContext.from_dict(context_dict)

    async def save(
        self, context: ConversationContext, ttl_seconds: int = DEFAULT_TTL_SECONDS
    ) -> None:
        """Save conversation context with TTL.

        Args:
            context: Conversation context to save
            ttl_seconds: Time-to-live in seconds (default 1 hour)
        """
        key = self._get_key(context.phone_number)
        # Serialize to JSON
        data = json.dumps(context.to_dict())

        # Store with expiry
        await self.redis.set(key, data, ex=ttl_seconds)

    async def delete(self, phone_number: str) -> None:
        """Delete conversation context.

        Args:
            phone_number: User's phone number
        """
        key = self._get_key(phone_number)
        await self.redis.delete(key)

    async def exists(self, phone_number: str) -> bool:
        """Check if conversation context exists.

        Args:
            phone_number: User's phone number

        Returns:
            True if context exists, False otherwise
        """
        key = self._get_key(phone_number)
        result: int = await self.redis.exists(key)  # type: ignore[assignment]
        return result > 0
