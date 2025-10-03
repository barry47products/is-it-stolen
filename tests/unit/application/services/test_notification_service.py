"""Unit tests for NotificationService."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch
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
    """Create notification service instance."""
    return NotificationService(
        whatsapp_client=mock_whatsapp_client,
        event_bus=event_bus,
    )


class TestNotificationService:
    """Test suite for NotificationService."""

    def test_subscribes_to_events_on_start(
        self,
        notification_service: NotificationService,
        event_bus: InMemoryEventBus,
    ) -> None:
        """Should subscribe to all domain events on start."""
        # Act
        notification_service.start()

        # Assert
        assert ItemReported in event_bus._handlers
        assert ItemVerified in event_bus._handlers
        assert ItemRecovered in event_bus._handlers
        assert ItemDeleted in event_bus._handlers
        assert ItemUpdated in event_bus._handlers

    def test_unsubscribes_from_events_on_stop(
        self,
        notification_service: NotificationService,
        event_bus: InMemoryEventBus,
    ) -> None:
        """Should unsubscribe from all events on stop."""
        # Arrange
        notification_service.start()

        # Act
        notification_service.stop()

        # Assert - handlers should be removed
        assert len(event_bus._handlers.get(ItemReported, [])) == 0
        assert len(event_bus._handlers.get(ItemVerified, [])) == 0
        assert len(event_bus._handlers.get(ItemRecovered, [])) == 0

    @pytest.mark.asyncio
    async def test_sends_report_confirmation(
        self,
        notification_service: NotificationService,
        event_bus: InMemoryEventBus,
        mock_whatsapp_client: AsyncMock,
    ) -> None:
        """Should send confirmation when item is reported."""
        # Arrange
        notification_service.start()
        event = ItemReported(
            report_id=uuid4(),
            reporter_phone=PhoneNumber("+27821234567"),
            item_type=ItemCategory.BICYCLE,
            description="Red mountain bike",
            stolen_date=datetime.now(UTC),
            location=Location(latitude=-33.9249, longitude=18.4241),
        )

        # Act
        await event_bus.publish(event)

        # Assert
        mock_whatsapp_client.send_text_message.assert_called_once()
        call_args = mock_whatsapp_client.send_text_message.call_args
        assert call_args[1]["to"] == "+27821234567"
        assert "Report ID" in call_args[1]["text"]
        assert str(event.report_id) in call_args[1]["text"]

    @pytest.mark.asyncio
    async def test_sends_verification_confirmation(
        self,
        notification_service: NotificationService,
        event_bus: InMemoryEventBus,
        mock_whatsapp_client: AsyncMock,
    ) -> None:
        """Should send confirmation when item is verified."""
        # Arrange
        notification_service.start()
        event = ItemVerified(
            report_id=uuid4(),
            police_reference="CR/2024/123456",
            verified_by=PhoneNumber("+27821234567"),
        )

        # Act
        await event_bus.publish(event)

        # Assert
        mock_whatsapp_client.send_text_message.assert_called_once()
        call_args = mock_whatsapp_client.send_text_message.call_args
        assert call_args[1]["to"] == "+27821234567"
        assert "verified" in call_args[1]["text"]
        assert "CR/2024/123456" in call_args[1]["text"]

    @pytest.mark.asyncio
    async def test_sends_recovery_confirmation(
        self,
        notification_service: NotificationService,
        event_bus: InMemoryEventBus,
        mock_whatsapp_client: AsyncMock,
    ) -> None:
        """Should send confirmation when item is recovered."""
        # Arrange
        notification_service.start()
        event = ItemRecovered(
            report_id=uuid4(),
            recovered_by=PhoneNumber("+27821234567"),
            recovery_location=Location(
                latitude=-33.9249,
                longitude=18.4241,
                address="Cape Town",
            ),
        )

        # Act
        await event_bus.publish(event)

        # Assert
        mock_whatsapp_client.send_text_message.assert_called_once()
        call_args = mock_whatsapp_client.send_text_message.call_args
        assert call_args[1]["to"] == "+27821234567"
        assert "recovered" in call_args[1]["text"]

    @pytest.mark.asyncio
    async def test_sends_deletion_confirmation(
        self,
        notification_service: NotificationService,
        event_bus: InMemoryEventBus,
        mock_whatsapp_client: AsyncMock,
    ) -> None:
        """Should send confirmation when item is deleted."""
        # Arrange
        notification_service.start()
        event = ItemDeleted(
            report_id=uuid4(),
            deleted_by=PhoneNumber("+27821234567"),
            reason="Duplicate",
        )

        # Act
        await event_bus.publish(event)

        # Assert
        mock_whatsapp_client.send_text_message.assert_called_once()
        call_args = mock_whatsapp_client.send_text_message.call_args
        assert call_args[1]["to"] == "+27821234567"
        assert "deleted" in call_args[1]["text"]

    @pytest.mark.asyncio
    async def test_sends_update_confirmation(
        self,
        notification_service: NotificationService,
        event_bus: InMemoryEventBus,
        mock_whatsapp_client: AsyncMock,
    ) -> None:
        """Should send confirmation when item is updated."""
        # Arrange
        notification_service.start()
        event = ItemUpdated(
            report_id=uuid4(),
            updated_by=PhoneNumber("+27821234567"),
            updated_fields={"description": "Updated description", "brand": "Trek"},
        )

        # Act
        await event_bus.publish(event)

        # Assert
        mock_whatsapp_client.send_text_message.assert_called_once()
        call_args = mock_whatsapp_client.send_text_message.call_args
        assert call_args[1]["to"] == "+27821234567"
        assert "updated" in call_args[1]["text"]
        assert "description" in call_args[1]["text"]

    @pytest.mark.asyncio
    async def test_handles_whatsapp_api_error_gracefully(
        self,
        notification_service: NotificationService,
        event_bus: InMemoryEventBus,
        mock_whatsapp_client: AsyncMock,
    ) -> None:
        """Should handle WhatsApp API errors without raising."""
        # Arrange
        notification_service.start()
        mock_whatsapp_client.send_text_message.side_effect = WhatsAppAPIError(
            "API Error"
        )
        event = ItemReported(
            report_id=uuid4(),
            reporter_phone=PhoneNumber("+27821234567"),
            item_type=ItemCategory.BICYCLE,
            description="Red mountain bike",
            stolen_date=datetime.now(UTC),
            location=Location(latitude=-33.9249, longitude=18.4241),
        )

        # Act - should not raise
        await event_bus.publish(event)

        # Assert
        mock_whatsapp_client.send_text_message.assert_called_once()

    @pytest.mark.asyncio
    async def test_handles_unexpected_error_gracefully(
        self,
        notification_service: NotificationService,
        event_bus: InMemoryEventBus,
        mock_whatsapp_client: AsyncMock,
    ) -> None:
        """Should handle unexpected errors without raising."""
        # Arrange
        notification_service.start()
        mock_whatsapp_client.send_text_message.side_effect = Exception(
            "Unexpected error"
        )
        event = ItemReported(
            report_id=uuid4(),
            reporter_phone=PhoneNumber("+27821234567"),
            item_type=ItemCategory.BICYCLE,
            description="Red mountain bike",
            stolen_date=datetime.now(UTC),
            location=Location(latitude=-33.9249, longitude=18.4241),
        )

        # Act - should not raise
        await event_bus.publish(event)

        # Assert
        mock_whatsapp_client.send_text_message.assert_called_once()

    @pytest.mark.asyncio
    async def test_logs_unexpected_error_in_verification_handler(
        self,
        notification_service: NotificationService,
        event_bus: InMemoryEventBus,
        mock_whatsapp_client: AsyncMock,
    ) -> None:
        """Should log unexpected errors in verification handler with exc_info."""
        # Arrange
        notification_service.start()
        mock_whatsapp_client.send_text_message.side_effect = Exception(
            "Unexpected error"
        )
        event = ItemVerified(
            report_id=uuid4(),
            police_reference="CR/2024/123456",
            verified_by=PhoneNumber("+27821234567"),
        )

        # Act & Assert
        with patch(
            "src.application.services.notification_service.logger"
        ) as mock_logger:
            await event_bus.publish(event)
            mock_logger.error.assert_called_once()
            call_args = mock_logger.error.call_args
            assert "Unexpected error" in call_args[0][0]
            assert call_args[1]["exc_info"] is True

    @pytest.mark.asyncio
    async def test_logs_unexpected_error_in_recovery_handler(
        self,
        notification_service: NotificationService,
        event_bus: InMemoryEventBus,
        mock_whatsapp_client: AsyncMock,
    ) -> None:
        """Should log unexpected errors in recovery handler with exc_info."""
        # Arrange
        notification_service.start()
        mock_whatsapp_client.send_text_message.side_effect = Exception(
            "Unexpected error"
        )
        event = ItemRecovered(
            report_id=uuid4(),
            recovered_by=PhoneNumber("+27821234567"),
            recovery_location=Location(latitude=-33.9249, longitude=18.4241),
        )

        # Act & Assert
        with patch(
            "src.application.services.notification_service.logger"
        ) as mock_logger:
            await event_bus.publish(event)
            mock_logger.error.assert_called_once()
            call_args = mock_logger.error.call_args
            assert "Unexpected error" in call_args[0][0]
            assert call_args[1]["exc_info"] is True

    @pytest.mark.asyncio
    async def test_logs_unexpected_error_in_deletion_handler(
        self,
        notification_service: NotificationService,
        event_bus: InMemoryEventBus,
        mock_whatsapp_client: AsyncMock,
    ) -> None:
        """Should log unexpected errors in deletion handler with exc_info."""
        # Arrange
        notification_service.start()
        mock_whatsapp_client.send_text_message.side_effect = Exception(
            "Unexpected error"
        )
        event = ItemDeleted(
            report_id=uuid4(),
            deleted_by=PhoneNumber("+27821234567"),
            reason="Duplicate",
        )

        # Act & Assert
        with patch(
            "src.application.services.notification_service.logger"
        ) as mock_logger:
            await event_bus.publish(event)
            mock_logger.error.assert_called_once()
            call_args = mock_logger.error.call_args
            assert "Unexpected error" in call_args[0][0]
            assert call_args[1]["exc_info"] is True

    @pytest.mark.asyncio
    async def test_logs_unexpected_error_in_update_handler(
        self,
        notification_service: NotificationService,
        event_bus: InMemoryEventBus,
        mock_whatsapp_client: AsyncMock,
    ) -> None:
        """Should log unexpected errors in update handler with exc_info."""
        # Arrange
        notification_service.start()
        mock_whatsapp_client.send_text_message.side_effect = Exception(
            "Unexpected error"
        )
        event = ItemUpdated(
            report_id=uuid4(),
            updated_by=PhoneNumber("+27821234567"),
            updated_fields={"description": "Updated"},
        )

        # Act & Assert
        with patch(
            "src.application.services.notification_service.logger"
        ) as mock_logger:
            await event_bus.publish(event)
            mock_logger.error.assert_called_once()
            call_args = mock_logger.error.call_args
            assert "Unexpected error" in call_args[0][0]
            assert call_args[1]["exc_info"] is True

    @pytest.mark.asyncio
    async def test_logs_whatsapp_api_error_in_verification_handler(
        self,
        notification_service: NotificationService,
        event_bus: InMemoryEventBus,
        mock_whatsapp_client: AsyncMock,
    ) -> None:
        """Should log WhatsApp API errors in verification handler with exc_info."""
        # Arrange
        notification_service.start()
        mock_whatsapp_client.send_text_message.side_effect = WhatsAppAPIError(
            "API Error"
        )
        event = ItemVerified(
            report_id=uuid4(),
            police_reference="CR/2024/123456",
            verified_by=PhoneNumber("+27821234567"),
        )

        # Act & Assert
        with patch(
            "src.application.services.notification_service.logger"
        ) as mock_logger:
            await event_bus.publish(event)
            mock_logger.error.assert_called_once()
            call_args = mock_logger.error.call_args
            assert "Failed to send verification confirmation" in call_args[0][0]
            assert call_args[1]["exc_info"] is True

    @pytest.mark.asyncio
    async def test_logs_whatsapp_api_error_in_recovery_handler(
        self,
        notification_service: NotificationService,
        event_bus: InMemoryEventBus,
        mock_whatsapp_client: AsyncMock,
    ) -> None:
        """Should log WhatsApp API errors in recovery handler with exc_info."""
        # Arrange
        notification_service.start()
        mock_whatsapp_client.send_text_message.side_effect = WhatsAppAPIError(
            "API Error"
        )
        event = ItemRecovered(
            report_id=uuid4(),
            recovered_by=PhoneNumber("+27821234567"),
            recovery_location=Location(latitude=-33.9249, longitude=18.4241),
        )

        # Act & Assert
        with patch(
            "src.application.services.notification_service.logger"
        ) as mock_logger:
            await event_bus.publish(event)
            mock_logger.error.assert_called_once()
            call_args = mock_logger.error.call_args
            assert "Failed to send recovery confirmation" in call_args[0][0]
            assert call_args[1]["exc_info"] is True

    @pytest.mark.asyncio
    async def test_logs_whatsapp_api_error_in_deletion_handler(
        self,
        notification_service: NotificationService,
        event_bus: InMemoryEventBus,
        mock_whatsapp_client: AsyncMock,
    ) -> None:
        """Should log WhatsApp API errors in deletion handler with exc_info."""
        # Arrange
        notification_service.start()
        mock_whatsapp_client.send_text_message.side_effect = WhatsAppAPIError(
            "API Error"
        )
        event = ItemDeleted(
            report_id=uuid4(),
            deleted_by=PhoneNumber("+27821234567"),
            reason="Duplicate",
        )

        # Act & Assert
        with patch(
            "src.application.services.notification_service.logger"
        ) as mock_logger:
            await event_bus.publish(event)
            mock_logger.error.assert_called_once()
            call_args = mock_logger.error.call_args
            assert "Failed to send deletion confirmation" in call_args[0][0]
            assert call_args[1]["exc_info"] is True

    @pytest.mark.asyncio
    async def test_logs_whatsapp_api_error_in_update_handler(
        self,
        notification_service: NotificationService,
        event_bus: InMemoryEventBus,
        mock_whatsapp_client: AsyncMock,
    ) -> None:
        """Should log WhatsApp API errors in update handler with exc_info."""
        # Arrange
        notification_service.start()
        mock_whatsapp_client.send_text_message.side_effect = WhatsAppAPIError(
            "API Error"
        )
        event = ItemUpdated(
            report_id=uuid4(),
            updated_by=PhoneNumber("+27821234567"),
            updated_fields={"description": "Updated"},
        )

        # Act & Assert
        with patch(
            "src.application.services.notification_service.logger"
        ) as mock_logger:
            await event_bus.publish(event)
            mock_logger.error.assert_called_once()
            call_args = mock_logger.error.call_args
            assert "Failed to send update confirmation" in call_args[0][0]
            assert call_args[1]["exc_info"] is True

    @pytest.mark.asyncio
    async def test_does_not_send_when_not_started(
        self,
        notification_service: NotificationService,
        event_bus: InMemoryEventBus,
        mock_whatsapp_client: AsyncMock,
    ) -> None:
        """Should not send notifications when service not started."""
        # Arrange - don't call start()
        event = ItemReported(
            report_id=uuid4(),
            reporter_phone=PhoneNumber("+27821234567"),
            item_type=ItemCategory.BICYCLE,
            description="Red mountain bike",
            stolen_date=datetime.now(UTC),
            location=Location(latitude=-33.9249, longitude=18.4241),
        )

        # Act
        await event_bus.publish(event)

        # Assert
        mock_whatsapp_client.send_text_message.assert_not_called()
