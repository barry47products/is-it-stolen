"""Tests for conversation storage."""

from unittest.mock import AsyncMock

import pytest

from src.presentation.bot.context import ConversationContext
from src.presentation.bot.states import ConversationState
from src.presentation.bot.storage import RedisConversationStorage


@pytest.mark.unit
class TestRedisConversationStorage:
    """Test Redis-based conversation storage."""

    @pytest.fixture
    def mock_redis(self) -> AsyncMock:
        """Create mock Redis client."""
        redis_mock = AsyncMock()
        redis_mock.get = AsyncMock(return_value=None)
        redis_mock.set = AsyncMock(return_value=True)
        redis_mock.delete = AsyncMock(return_value=1)
        return redis_mock

    @pytest.fixture
    def storage(self, mock_redis: AsyncMock) -> RedisConversationStorage:
        """Create storage with mock Redis."""
        return RedisConversationStorage(redis_client=mock_redis)

    @pytest.mark.asyncio
    async def test_get_returns_none_when_no_context_exists(
        self, storage: RedisConversationStorage, mock_redis: AsyncMock
    ) -> None:
        """Test get returns None when context doesn't exist."""
        # Arrange
        phone_number = "+1234567890"
        mock_redis.get.return_value = None

        # Act
        result = await storage.get(phone_number)

        # Assert
        assert result is None
        mock_redis.get.assert_called_once_with("conversation:+1234567890")

    @pytest.mark.asyncio
    async def test_get_returns_context_when_exists(
        self, storage: RedisConversationStorage, mock_redis: AsyncMock
    ) -> None:
        """Test get returns deserialized context."""
        # Arrange
        phone_number = "+1234567890"
        stored_data = {
            "phone_number": "+1234567890",
            "state": "main_menu",
            "data": {"action": "check"},
            "created_at": "2025-01-01T00:00:00+00:00",
            "updated_at": "2025-01-01T00:01:00+00:00",
        }
        import json

        mock_redis.get.return_value = json.dumps(stored_data)

        # Act
        result = await storage.get(phone_number)

        # Assert
        assert result is not None
        assert result.phone_number == "+1234567890"
        assert result.state == ConversationState.MAIN_MENU
        assert result.data == {"action": "check"}

    @pytest.mark.asyncio
    async def test_save_stores_serialized_context(
        self, storage: RedisConversationStorage, mock_redis: AsyncMock
    ) -> None:
        """Test save stores context in Redis with TTL."""
        # Arrange
        context = ConversationContext(
            phone_number="+1234567890",
            state=ConversationState.MAIN_MENU,
            data={"action": "check"},
        )

        # Act
        await storage.save(context)

        # Assert
        mock_redis.set.assert_called_once()
        call_args = mock_redis.set.call_args
        assert call_args[0][0] == "conversation:+1234567890"  # key
        assert "main_menu" in call_args[0][1]  # serialized context
        assert call_args[1]["ex"] == 3600  # TTL in seconds

    @pytest.mark.asyncio
    async def test_save_with_custom_ttl(
        self, storage: RedisConversationStorage, mock_redis: AsyncMock
    ) -> None:
        """Test save with custom TTL."""
        # Arrange
        context = ConversationContext(phone_number="+1234567890")
        custom_ttl = 7200

        # Act
        await storage.save(context, ttl_seconds=custom_ttl)

        # Assert
        call_args = mock_redis.set.call_args
        assert call_args[1]["ex"] == 7200

    @pytest.mark.asyncio
    async def test_delete_removes_context(
        self, storage: RedisConversationStorage, mock_redis: AsyncMock
    ) -> None:
        """Test delete removes context from Redis."""
        # Arrange
        phone_number = "+1234567890"

        # Act
        await storage.delete(phone_number)

        # Assert
        mock_redis.delete.assert_called_once_with("conversation:+1234567890")

    @pytest.mark.asyncio
    async def test_exists_returns_true_when_context_exists(
        self, storage: RedisConversationStorage, mock_redis: AsyncMock
    ) -> None:
        """Test exists returns True when context exists."""
        # Arrange
        phone_number = "+1234567890"
        mock_redis.exists = AsyncMock(return_value=1)

        # Act
        result = await storage.exists(phone_number)

        # Assert
        assert result is True
        mock_redis.exists.assert_called_once_with("conversation:+1234567890")

    @pytest.mark.asyncio
    async def test_exists_returns_false_when_no_context(
        self, storage: RedisConversationStorage, mock_redis: AsyncMock
    ) -> None:
        """Test exists returns False when context doesn't exist."""
        # Arrange
        phone_number = "+1234567890"
        mock_redis.exists = AsyncMock(return_value=0)

        # Act
        result = await storage.exists(phone_number)

        # Assert
        assert result is False

    def test_generates_correct_key_format(
        self, storage: RedisConversationStorage
    ) -> None:
        """Test key generation uses correct format."""
        # Arrange
        phone_number = "+1234567890"

        # Act
        key = storage._get_key(phone_number)

        # Assert
        assert key == "conversation:+1234567890"
