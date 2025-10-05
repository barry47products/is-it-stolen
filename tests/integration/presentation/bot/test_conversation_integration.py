"""Integration tests for conversation state machine with real Redis."""

import pytest
from redis.asyncio import Redis

from src.infrastructure.config.settings import get_settings
from src.presentation.bot.context import ConversationContext
from src.presentation.bot.state_machine import ConversationStateMachine
from src.presentation.bot.states import ConversationState
from src.presentation.bot.storage import RedisConversationStorage


@pytest.mark.integration
class TestConversationIntegration:
    """Test conversation state machine with real Redis."""

    @pytest.fixture
    async def redis_client(  # type: ignore[misc]
        self,
    ) -> Redis:  # type: ignore[type-arg]
        """Create real Redis client for testing."""
        settings = get_settings()
        client = Redis.from_url(str(settings.redis_url))
        yield client
        await client.aclose()

    @pytest.fixture
    async def storage(
        self,
        redis_client: Redis,  # type: ignore[type-arg]
    ) -> RedisConversationStorage:
        """Create storage with real Redis."""
        return RedisConversationStorage(redis_client=redis_client)

    @pytest.fixture
    async def state_machine(
        self, storage: RedisConversationStorage
    ) -> ConversationStateMachine:
        """Create state machine with real storage."""
        return ConversationStateMachine(storage=storage)

    @pytest.mark.asyncio
    async def test_full_conversation_flow(
        self,
        state_machine: ConversationStateMachine,
        storage: RedisConversationStorage,
    ) -> None:
        """Test complete conversation flow with Redis."""
        # Arrange
        phone_number = "+1234567890"

        try:
            # Act & Assert: Get or create new conversation
            context = await state_machine.get_or_create(phone_number)
            assert context.state == ConversationState.IDLE
            assert await storage.exists(phone_number) is False  # Not saved yet

            # Transition to main menu
            context = await state_machine.transition(
                context, ConversationState.MAIN_MENU
            )
            assert context.state == ConversationState.MAIN_MENU
            assert await storage.exists(phone_number) is True

            # Verify persistence: retrieve from storage
            retrieved = await storage.get(phone_number)
            assert retrieved is not None
            assert retrieved.state == ConversationState.MAIN_MENU

            # Add data and transition to checking flow
            context = await state_machine.update_data(context, {"action": "check"})
            context = await state_machine.transition(
                context, ConversationState.CHECKING_CATEGORY
            )

            # Verify data persisted
            retrieved = await storage.get(phone_number)
            assert retrieved is not None
            assert retrieved.data == {"action": "check"}
            assert retrieved.state == ConversationState.CHECKING_CATEGORY

            # Complete conversation
            context = await state_machine.complete(context)
            assert context.state == ConversationState.COMPLETE

            # Verify deleted from storage after completion
            assert await storage.exists(phone_number) is False

        finally:
            # Cleanup
            await storage.delete(phone_number)

    @pytest.mark.asyncio
    async def test_conversation_with_cancel(
        self,
        state_machine: ConversationStateMachine,
        storage: RedisConversationStorage,
    ) -> None:
        """Test cancelling a conversation."""
        # Arrange
        phone_number = "+1234567891"

        try:
            # Act: Start conversation
            context = await state_machine.get_or_create(phone_number)
            context = await state_machine.transition(
                context, ConversationState.MAIN_MENU
            )

            # Cancel
            context = await state_machine.cancel(context)

            # Assert
            assert context.state == ConversationState.CANCELLED
            assert await storage.exists(phone_number) is False

        finally:
            # Cleanup
            await storage.delete(phone_number)

    @pytest.mark.asyncio
    async def test_conversation_ttl(
        self,
        redis_client: Redis,  # type: ignore[type-arg]
    ) -> None:
        """Test conversation TTL is set correctly in Redis."""
        # Arrange
        phone_number = "+1234567892"
        storage = RedisConversationStorage(redis_client=redis_client)
        key = f"conversation:{phone_number}"

        try:
            # Act: Create and save with short TTL
            context = ConversationContext(
                phone_number=phone_number, state=ConversationState.MAIN_MENU
            )
            await storage.save(context, ttl_seconds=300)

            # Assert: Key exists and has TTL set
            assert await storage.exists(phone_number) is True
            ttl = await redis_client.ttl(key)
            assert ttl > 0  # TTL is set
            assert ttl <= 300  # TTL is not greater than what we set

        finally:
            # Cleanup
            await storage.delete(phone_number)

    @pytest.mark.asyncio
    async def test_multiple_concurrent_conversations(
        self,
        state_machine: ConversationStateMachine,
        storage: RedisConversationStorage,
    ) -> None:
        """Test multiple users can have concurrent conversations."""
        # Arrange
        phone1 = "+1111111111"
        phone2 = "+2222222222"

        try:
            # Act: Create two conversations
            context1 = await state_machine.get_or_create(phone1)
            context1 = await state_machine.transition(
                context1, ConversationState.MAIN_MENU
            )
            context1 = await state_machine.update_data(context1, {"user": "user1"})

            context2 = await state_machine.get_or_create(phone2)
            context2 = await state_machine.transition(
                context2, ConversationState.MAIN_MENU
            )
            context2 = await state_machine.transition(
                context2, ConversationState.REPORTING_CATEGORY
            )
            context2 = await state_machine.update_data(context2, {"user": "user2"})

            # Assert: Both exist independently
            retrieved1 = await storage.get(phone1)
            retrieved2 = await storage.get(phone2)

            assert retrieved1 is not None
            assert retrieved2 is not None
            assert retrieved1.data == {"user": "user1"}
            assert retrieved2.data == {"user": "user2"}
            assert retrieved1.state == ConversationState.MAIN_MENU
            assert retrieved2.state == ConversationState.REPORTING_CATEGORY

        finally:
            # Cleanup
            await storage.delete(phone1)
            await storage.delete(phone2)
