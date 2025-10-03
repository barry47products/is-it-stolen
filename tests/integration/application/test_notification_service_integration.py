"""Integration tests for NotificationService with real event bus."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from src.application.services.notification_service import NotificationService
from src.domain.events.domain_events import (
    ItemDeleted,
    ItemRecovered,
    ItemReported,
    ItemUpdated,
    ItemVerified,
)
from src.domain.value_objects.item_category import ItemCategory
from src.domain.value_objects.location import Location
from src.domain.value_objects.phone_number import PhoneNumber
from src.infrastructure.messaging.event_bus import InMemoryEventBus
from src.infrastructure.whatsapp.client import WhatsAppClient
from src.infrastructure.whatsapp.exceptions import WhatsAppAPIError


@pytest.fixture
def mock_whatsapp_client() -> AsyncMock:
    """Create mock WhatsApp client."""
    client = AsyncMock(spec=WhatsAppClient)
    client.send_text_message = AsyncMock(return_value="msg_123")
    return client


@pytest.fixture
def event_bus() -> InMemoryEventBus:
    """Create real event bus."""
    return InMemoryEventBus()


@pytest.fixture
def notification_service(
    mock_whatsapp_client: AsyncMock,
    event_bus: InMemoryEventBus,
) -> NotificationService:
    """Create notification service with real event bus."""
    service = NotificationService(
        whatsapp_client=mock_whatsapp_client,
        event_bus=event_bus,
    )
    service.start()
    return service


@pytest.mark.integration
@pytest.mark.asyncio
class TestNotificationServiceIntegration:
    """Integration tests for NotificationService with real event bus."""

    async def test_handles_multiple_events_in_sequence(
        self,
        notification_service: NotificationService,
        event_bus: InMemoryEventBus,
        mock_whatsapp_client: AsyncMock,
    ) -> None:
        """Should handle multiple events published in sequence."""
        # Arrange
        report_id = uuid4()
        phone = PhoneNumber("+27821234567")

        event1 = ItemReported(
            report_id=report_id,
            reporter_phone=phone,
            item_type=ItemCategory.BICYCLE,
            description="Red bike",
            stolen_date=datetime.now(UTC),
            location=Location(latitude=-33.9249, longitude=18.4241),
        )

        event2 = ItemVerified(
            report_id=report_id,
            police_reference="CR/2024/123456",
            verified_by=phone,
        )

        event3 = ItemRecovered(
            report_id=report_id,
            recovered_by=phone,
            recovery_location=Location(latitude=-33.9249, longitude=18.4241),
        )

        # Act
        await event_bus.publish(event1)
        await event_bus.publish(event2)
        await event_bus.publish(event3)

        # Assert
        assert mock_whatsapp_client.send_text_message.call_count == 3

    async def test_multiple_services_receive_same_event(
        self,
        event_bus: InMemoryEventBus,
        mock_whatsapp_client: AsyncMock,
    ) -> None:
        """Should allow multiple services to receive the same event."""
        # Arrange
        service1 = NotificationService(
            whatsapp_client=mock_whatsapp_client,
            event_bus=event_bus,
        )
        service2 = NotificationService(
            whatsapp_client=mock_whatsapp_client,
            event_bus=event_bus,
        )

        service1.start()
        service2.start()

        event = ItemReported(
            report_id=uuid4(),
            reporter_phone=PhoneNumber("+27821234567"),
            item_type=ItemCategory.BICYCLE,
            description="Red bike",
            stolen_date=datetime.now(UTC),
            location=Location(latitude=-33.9249, longitude=18.4241),
        )

        # Act
        await event_bus.publish(event)

        # Assert - both services should have received the event
        assert mock_whatsapp_client.send_text_message.call_count == 2

    async def test_service_lifecycle_start_stop(
        self,
        mock_whatsapp_client: AsyncMock,
        event_bus: InMemoryEventBus,
    ) -> None:
        """Should properly handle service lifecycle."""
        # Arrange
        service = NotificationService(
            whatsapp_client=mock_whatsapp_client,
            event_bus=event_bus,
        )

        event = ItemReported(
            report_id=uuid4(),
            reporter_phone=PhoneNumber("+27821234567"),
            item_type=ItemCategory.BICYCLE,
            description="Red bike",
            stolen_date=datetime.now(UTC),
            location=Location(latitude=-33.9249, longitude=18.4241),
        )

        # Act - publish before starting (should not receive)
        await event_bus.publish(event)
        assert mock_whatsapp_client.send_text_message.call_count == 0

        # Act - start and publish (should receive)
        service.start()
        await event_bus.publish(event)
        assert mock_whatsapp_client.send_text_message.call_count == 1

        # Act - stop and publish (should not receive)
        service.stop()
        await event_bus.publish(event)
        assert mock_whatsapp_client.send_text_message.call_count == 1

    async def test_different_event_types_trigger_different_messages(
        self,
        notification_service: NotificationService,
        event_bus: InMemoryEventBus,
        mock_whatsapp_client: AsyncMock,
    ) -> None:
        """Should send different messages for different event types."""
        # Arrange
        report_id = uuid4()
        phone = PhoneNumber("+27821234567")

        reported_event = ItemReported(
            report_id=report_id,
            reporter_phone=phone,
            item_type=ItemCategory.BICYCLE,
            description="Red bike",
            stolen_date=datetime.now(UTC),
            location=Location(latitude=-33.9249, longitude=18.4241),
        )

        deleted_event = ItemDeleted(
            report_id=report_id,
            deleted_by=phone,
            reason="Duplicate",
        )

        # Act
        await event_bus.publish(reported_event)
        await event_bus.publish(deleted_event)

        # Assert - different messages sent
        assert mock_whatsapp_client.send_text_message.call_count == 2

        first_call = mock_whatsapp_client.send_text_message.call_args_list[0]
        second_call = mock_whatsapp_client.send_text_message.call_args_list[1]

        assert "reported successfully" in first_call[1]["text"]
        assert "deleted successfully" in second_call[1]["text"]

    async def test_event_with_all_optional_fields(
        self,
        notification_service: NotificationService,
        event_bus: InMemoryEventBus,
        mock_whatsapp_client: AsyncMock,
    ) -> None:
        """Should handle events with all optional fields populated."""
        # Arrange
        event = ItemReported(
            report_id=uuid4(),
            reporter_phone=PhoneNumber("+27821234567"),
            item_type=ItemCategory.BICYCLE,
            description="Red mountain bike",
            stolen_date=datetime.now(UTC),
            location=Location(
                latitude=-33.9249,
                longitude=18.4241,
                address="Cape Town, South Africa",
            ),
            brand="Trek",
            model="X-Caliber 8",
            serial_number="WTU123456",
            color="Red",
        )

        # Act
        await event_bus.publish(event)

        # Assert
        mock_whatsapp_client.send_text_message.assert_called_once()
        call_args = mock_whatsapp_client.send_text_message.call_args
        assert "Red mountain bike" in call_args[1]["text"]

    async def test_handles_whatsapp_api_error_in_verification_notification(
        self,
        notification_service: NotificationService,
        event_bus: InMemoryEventBus,
        mock_whatsapp_client: AsyncMock,
    ) -> None:
        """Should handle WhatsApp API error when sending verification notification."""
        # Arrange
        mock_whatsapp_client.send_text_message.side_effect = WhatsAppAPIError(
            "API Error"
        )
        event = ItemVerified(
            report_id=uuid4(),
            police_reference="CR/2024/123456",
            verified_by=PhoneNumber("+27821234567"),
        )

        # Act - should not raise
        await event_bus.publish(event)

        # Assert
        mock_whatsapp_client.send_text_message.assert_called_once()

    async def test_handles_unexpected_error_in_recovery_notification(
        self,
        notification_service: NotificationService,
        event_bus: InMemoryEventBus,
        mock_whatsapp_client: AsyncMock,
    ) -> None:
        """Should handle unexpected error when sending recovery notification."""
        # Arrange
        mock_whatsapp_client.send_text_message.side_effect = Exception(
            "Unexpected error"
        )
        event = ItemRecovered(
            report_id=uuid4(),
            recovered_by=PhoneNumber("+27821234567"),
            recovery_location=Location(latitude=-33.9249, longitude=18.4241),
        )

        # Act - should not raise
        await event_bus.publish(event)

        # Assert
        mock_whatsapp_client.send_text_message.assert_called_once()

    async def test_handles_whatsapp_api_error_in_deletion_notification(
        self,
        notification_service: NotificationService,
        event_bus: InMemoryEventBus,
        mock_whatsapp_client: AsyncMock,
    ) -> None:
        """Should handle WhatsApp API error when sending deletion notification."""
        # Arrange
        mock_whatsapp_client.send_text_message.side_effect = WhatsAppAPIError(
            "API Error"
        )
        event = ItemDeleted(
            report_id=uuid4(),
            deleted_by=PhoneNumber("+27821234567"),
            reason="Duplicate",
        )

        # Act - should not raise
        await event_bus.publish(event)

        # Assert
        mock_whatsapp_client.send_text_message.assert_called_once()

    async def test_handles_unexpected_error_in_update_notification(
        self,
        notification_service: NotificationService,
        event_bus: InMemoryEventBus,
        mock_whatsapp_client: AsyncMock,
    ) -> None:
        """Should handle unexpected error when sending update notification."""
        # Arrange
        mock_whatsapp_client.send_text_message.side_effect = Exception(
            "Unexpected error"
        )
        event = ItemUpdated(
            report_id=uuid4(),
            updated_by=PhoneNumber("+27821234567"),
            updated_fields={"description": "Updated"},
        )

        # Act - should not raise
        await event_bus.publish(event)

        # Assert
        mock_whatsapp_client.send_text_message.assert_called_once()
