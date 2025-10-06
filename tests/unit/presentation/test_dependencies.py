"""Tests for dependency injection functions."""

import pytest

from src.domain.services.matching_service import ItemMatchingService
from src.domain.services.verification_service import VerificationService
from src.infrastructure.messaging.event_bus import InMemoryEventBus
from src.infrastructure.persistence.repositories.postgres_stolen_item_repository import (
    PostgresStolenItemRepository,
)
from src.infrastructure.whatsapp.client import WhatsAppClient
from src.presentation.api.dependencies import (
    get_conversation_storage,
    get_event_bus,
    get_ip_rate_limiter,
    get_matching_service,
    get_message_processor,
    get_redis_client,
    get_repository,
    get_state_machine,
    get_verification_service,
    get_whatsapp_client,
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

    def test_get_whatsapp_client_returns_client(self) -> None:
        """Test get_whatsapp_client returns client instance."""
        # Act
        client = get_whatsapp_client()

        # Assert
        assert isinstance(client, WhatsAppClient)

    def test_get_whatsapp_client_returns_singleton(self) -> None:
        """Test get_whatsapp_client returns same instance."""
        # Act
        client1 = get_whatsapp_client()
        client2 = get_whatsapp_client()

        # Assert
        assert client1 is client2

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

    def test_get_ip_rate_limiter_returns_rate_limiter(self) -> None:
        """Test get_ip_rate_limiter returns rate limiter instance."""
        from src.infrastructure.cache.rate_limiter import RateLimiter

        # Act
        rate_limiter = get_ip_rate_limiter()

        # Assert
        assert isinstance(rate_limiter, RateLimiter)

    def test_get_ip_rate_limiter_returns_singleton(self) -> None:
        """Test get_ip_rate_limiter returns same instance."""
        # Act
        limiter1 = get_ip_rate_limiter()
        limiter2 = get_ip_rate_limiter()

        # Assert
        assert limiter1 is limiter2

    def test_get_ip_rate_limiter_with_bypass_config(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test IP rate limiter parses bypass configuration correctly."""
        from src.infrastructure.cache.rate_limiter import RateLimiter
        from src.infrastructure.config.settings import Settings
        from src.presentation.api import dependencies

        # Reset singleton
        dependencies._ip_rate_limiter = None

        # Mock settings with bypass enabled
        mock_settings = Settings(
            database_url="postgresql://test:test@localhost/test",
            rate_limit_bypass_enabled=True,
            rate_limit_bypass_keys="+1234567890,192.168.1.1, test_ip",
        )
        monkeypatch.setattr(dependencies, "get_settings", lambda: mock_settings)

        # Act
        limiter = get_ip_rate_limiter()

        # Assert
        assert isinstance(limiter, RateLimiter)
        assert limiter.bypass_enabled is True
        assert "+1234567890" in limiter.bypass_keys
        assert "192.168.1.1" in limiter.bypass_keys
        assert "test_ip" in limiter.bypass_keys
        assert len(limiter.bypass_keys) == 3

        # Cleanup
        dependencies._ip_rate_limiter = None
