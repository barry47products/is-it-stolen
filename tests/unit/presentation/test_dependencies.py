"""Tests for dependency injection functions."""

import pytest

from src.domain.services.matching_service import ItemMatchingService
from src.domain.services.verification_service import VerificationService
from src.infrastructure.messaging.event_bus import InMemoryEventBus
from src.infrastructure.persistence.repositories.postgres_stolen_item_repository import (
    PostgresStolenItemRepository,
)
from src.presentation.api.dependencies import (
    get_conversation_storage,
    get_event_bus,
    get_matching_service,
    get_message_processor,
    get_redis_client,
    get_repository,
    get_state_machine,
    get_verification_service,
)
from src.presentation.bot.message_processor import MessageProcessor
from src.presentation.bot.state_machine import ConversationStateMachine
from src.presentation.bot.storage import RedisConversationStorage


@pytest.mark.unit
class TestDependencies:
    """Test dependency injection functions."""

    def test_get_redis_client_returns_client(self) -> None:
        """Test get_redis_client returns Redis client."""
        # Act
        client = get_redis_client()

        # Assert
        assert client is not None
        assert hasattr(client, "get")
        assert hasattr(client, "set")

    def test_get_redis_client_returns_singleton(self) -> None:
        """Test get_redis_client returns same instance."""
        # Act
        client1 = get_redis_client()
        client2 = get_redis_client()

        # Assert
        assert client1 is client2

    def test_get_conversation_storage_returns_storage(self) -> None:
        """Test get_conversation_storage returns storage instance."""
        # Act
        storage = get_conversation_storage()

        # Assert
        assert isinstance(storage, RedisConversationStorage)

    def test_get_conversation_storage_returns_singleton(self) -> None:
        """Test get_conversation_storage returns same instance."""
        # Act
        storage1 = get_conversation_storage()
        storage2 = get_conversation_storage()

        # Assert
        assert storage1 is storage2

    def test_get_state_machine_returns_state_machine(self) -> None:
        """Test get_state_machine returns state machine instance."""
        # Act
        state_machine = get_state_machine()

        # Assert
        assert isinstance(state_machine, ConversationStateMachine)

    def test_get_state_machine_returns_singleton(self) -> None:
        """Test get_state_machine returns same instance."""
        # Act
        machine1 = get_state_machine()
        machine2 = get_state_machine()

        # Assert
        assert machine1 is machine2

    def test_get_message_processor_returns_processor(self) -> None:
        """Test get_message_processor returns processor instance."""
        # Act
        processor = get_message_processor()

        # Assert
        assert isinstance(processor, MessageProcessor)

    def test_get_message_processor_returns_singleton(self) -> None:
        """Test get_message_processor returns same instance."""
        # Act
        processor1 = get_message_processor()
        processor2 = get_message_processor()

        # Assert
        assert processor1 is processor2

    def test_get_event_bus_returns_event_bus(self) -> None:
        """Test get_event_bus returns event bus instance."""
        # Act
        event_bus = get_event_bus()

        # Assert
        assert isinstance(event_bus, InMemoryEventBus)

    def test_get_event_bus_returns_singleton(self) -> None:
        """Test get_event_bus returns same instance."""
        # Act
        bus1 = get_event_bus()
        bus2 = get_event_bus()

        # Assert
        assert bus1 is bus2

    def test_get_matching_service_returns_service(self) -> None:
        """Test get_matching_service returns service instance."""
        # Act
        service = get_matching_service()

        # Assert
        assert isinstance(service, ItemMatchingService)

    def test_get_matching_service_returns_singleton(self) -> None:
        """Test get_matching_service returns same instance."""
        # Act
        service1 = get_matching_service()
        service2 = get_matching_service()

        # Assert
        assert service1 is service2

    def test_get_verification_service_returns_service(self) -> None:
        """Test get_verification_service returns service instance."""
        # Act
        service = get_verification_service()

        # Assert
        assert isinstance(service, VerificationService)

    def test_get_verification_service_returns_singleton(self) -> None:
        """Test get_verification_service returns same instance."""
        # Act
        service1 = get_verification_service()
        service2 = get_verification_service()

        # Assert
        assert service1 is service2

    @pytest.mark.asyncio
    async def test_get_repository_returns_repository(self) -> None:
        """Test get_repository returns repository instance."""
        # Act
        async for repo in get_repository():
            # Assert
            assert isinstance(repo, PostgresStolenItemRepository)
            break  # Only test first yield
