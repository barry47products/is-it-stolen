"""Unit tests for event bus."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from src.domain.events.domain_events import ItemReported
from src.domain.value_objects.item_category import ItemCategory
from src.domain.value_objects.location import Location
from src.domain.value_objects.phone_number import PhoneNumber
from src.infrastructure.messaging.event_bus import InMemoryEventBus


class TestInMemoryEventBus:
    """Test in-memory event bus implementation."""

    @pytest.fixture
    def event_bus(self) -> InMemoryEventBus:
        """Create event bus for testing."""
        return InMemoryEventBus()

    async def test_publishes_event_to_single_subscriber(
        self, event_bus: InMemoryEventBus
    ) -> None:
        """Should publish event to registered subscriber."""
        # Arrange
        handler = AsyncMock()
        event_bus.subscribe(ItemReported, handler)

        event = ItemReported(
            report_id=uuid4(),
            reporter_phone=PhoneNumber("+27123456789"),
            item_type=ItemCategory.BICYCLE,
            description="Red mountain bike",
            stolen_date=datetime.now(UTC),
            location=Location(latitude=-33.9249, longitude=18.4241),
        )

        # Act
        await event_bus.publish(event)

        # Assert
        handler.assert_called_once_with(event)

    async def test_publishes_event_to_multiple_subscribers(
        self, event_bus: InMemoryEventBus
    ) -> None:
        """Should publish event to all registered subscribers."""
        # Arrange
        handler1 = AsyncMock()
        handler2 = AsyncMock()
        event_bus.subscribe(ItemReported, handler1)
        event_bus.subscribe(ItemReported, handler2)

        event = ItemReported(
            report_id=uuid4(),
            reporter_phone=PhoneNumber("+27123456789"),
            item_type=ItemCategory.BICYCLE,
            description="Red mountain bike",
            stolen_date=datetime.now(UTC),
            location=Location(latitude=-33.9249, longitude=18.4241),
        )

        # Act
        await event_bus.publish(event)

        # Assert
        handler1.assert_called_once_with(event)
        handler2.assert_called_once_with(event)

    async def test_does_not_publish_to_unsubscribed_handlers(
        self, event_bus: InMemoryEventBus
    ) -> None:
        """Should not call handlers for different event types."""
        # Arrange
        from src.domain.events.domain_events import ItemVerified

        reported_handler = AsyncMock()
        verified_handler = AsyncMock()
        event_bus.subscribe(ItemReported, reported_handler)
        event_bus.subscribe(ItemVerified, verified_handler)

        event = ItemReported(
            report_id=uuid4(),
            reporter_phone=PhoneNumber("+27123456789"),
            item_type=ItemCategory.BICYCLE,
            description="Red mountain bike",
            stolen_date=datetime.now(UTC),
            location=Location(latitude=-33.9249, longitude=18.4241),
        )

        # Act
        await event_bus.publish(event)

        # Assert
        reported_handler.assert_called_once_with(event)
        verified_handler.assert_not_called()

    async def test_unsubscribe_removes_handler(
        self, event_bus: InMemoryEventBus
    ) -> None:
        """Should not call handler after unsubscribing."""
        # Arrange
        handler = AsyncMock()
        event_bus.subscribe(ItemReported, handler)
        event_bus.unsubscribe(ItemReported, handler)

        event = ItemReported(
            report_id=uuid4(),
            reporter_phone=PhoneNumber("+27123456789"),
            item_type=ItemCategory.BICYCLE,
            description="Red mountain bike",
            stolen_date=datetime.now(UTC),
            location=Location(latitude=-33.9249, longitude=18.4241),
        )

        # Act
        await event_bus.publish(event)

        # Assert
        handler.assert_not_called()

    async def test_handles_handler_exception_without_stopping_other_handlers(
        self, event_bus: InMemoryEventBus
    ) -> None:
        """Should continue publishing to other handlers when one fails."""
        # Arrange
        failing_handler = AsyncMock(side_effect=Exception("Handler failed"))
        successful_handler = AsyncMock()
        event_bus.subscribe(ItemReported, failing_handler)
        event_bus.subscribe(ItemReported, successful_handler)

        event = ItemReported(
            report_id=uuid4(),
            reporter_phone=PhoneNumber("+27123456789"),
            item_type=ItemCategory.BICYCLE,
            description="Red mountain bike",
            stolen_date=datetime.now(UTC),
            location=Location(latitude=-33.9249, longitude=18.4241),
        )

        # Act
        await event_bus.publish(event)

        # Assert
        failing_handler.assert_called_once_with(event)
        successful_handler.assert_called_once_with(event)

    async def test_publishes_to_no_handlers_without_error(
        self, event_bus: InMemoryEventBus
    ) -> None:
        """Should handle publishing when no handlers are registered."""
        # Arrange
        event = ItemReported(
            report_id=uuid4(),
            reporter_phone=PhoneNumber("+27123456789"),
            item_type=ItemCategory.BICYCLE,
            description="Red mountain bike",
            stolen_date=datetime.now(UTC),
            location=Location(latitude=-33.9249, longitude=18.4241),
        )

        # Act & Assert - Should not raise error
        await event_bus.publish(event)

    async def test_unsubscribe_non_existent_handler_does_not_raise_error(
        self, event_bus: InMemoryEventBus
    ) -> None:
        """Should handle unsubscribing handler that was never subscribed."""
        # Arrange
        handler = AsyncMock()

        # Act & Assert - Should not raise error
        event_bus.unsubscribe(ItemReported, handler)
