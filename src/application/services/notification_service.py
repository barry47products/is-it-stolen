"""Notification service for sending WhatsApp confirmations."""

import logging

from src.domain.events.domain_events import (
    ItemDeleted,
    ItemRecovered,
    ItemReported,
    ItemUpdated,
    ItemVerified,
)
from src.infrastructure.messaging.event_bus import InMemoryEventBus
from src.infrastructure.whatsapp.client import WhatsAppClient
from src.infrastructure.whatsapp.exceptions import WhatsAppAPIError

logger = logging.getLogger(__name__)


class NotificationService:
    """Service for sending WhatsApp notifications based on domain events.

    This service subscribes to domain events and sends appropriate WhatsApp
    messages to users. It handles failures gracefully and logs errors.
    """

    def __init__(
        self,
        whatsapp_client: WhatsAppClient,
        event_bus: InMemoryEventBus,
    ) -> None:
        """Initialize notification service.

        Args:
            whatsapp_client: WhatsApp client for sending messages
            event_bus: Event bus to subscribe to domain events
        """
        self.whatsapp_client = whatsapp_client
        self.event_bus = event_bus

    def start(self) -> None:
        """Start the notification service by subscribing to domain events."""
        self.event_bus.subscribe(ItemReported, self._handle_item_reported)
        self.event_bus.subscribe(ItemVerified, self._handle_item_verified)
        self.event_bus.subscribe(ItemRecovered, self._handle_item_recovered)
        self.event_bus.subscribe(ItemDeleted, self._handle_item_deleted)
        self.event_bus.subscribe(ItemUpdated, self._handle_item_updated)

    def stop(self) -> None:
        """Stop the notification service by unsubscribing from events."""
        self.event_bus.unsubscribe(ItemReported, self._handle_item_reported)
        self.event_bus.unsubscribe(ItemVerified, self._handle_item_verified)
        self.event_bus.unsubscribe(ItemRecovered, self._handle_item_recovered)
        self.event_bus.unsubscribe(ItemDeleted, self._handle_item_deleted)
        self.event_bus.unsubscribe(ItemUpdated, self._handle_item_updated)

    async def _handle_item_reported(self, event: ItemReported) -> None:
        """Handle ItemReported event by sending confirmation.

        Args:
            event: ItemReported domain event
        """
        try:
            message = (
                f"✅ Your stolen item has been reported successfully!\n\n"
                f"📋 Report ID: {event.report_id}\n"
                f"📦 Item: {event.item_type.value.title()}\n"
                f"📝 Description: {event.description}\n\n"
                f"We'll notify you if anyone reports finding a matching item."
            )

            await self.whatsapp_client.send_text_message(
                to=event.reporter_phone.value,
                text=message,
            )

            logger.info(f"Sent report confirmation for {event.report_id}")

        except WhatsAppAPIError as e:
            logger.error(
                f"Failed to send report confirmation for {event.report_id}: {e}",
                exc_info=True,
            )
        except Exception as e:
            logger.error(
                f"Unexpected error sending report confirmation: {e}",
                exc_info=True,
            )

    async def _handle_item_verified(self, event: ItemVerified) -> None:
        """Handle ItemVerified event by sending confirmation.

        Args:
            event: ItemVerified domain event
        """
        try:
            message = (
                f"✅ Your report has been verified!\n\n"
                f"📋 Report ID: {event.report_id}\n"
                f"🔍 Police Reference: {event.police_reference}\n\n"
                f"Your report is now marked as officially verified."
            )

            await self.whatsapp_client.send_text_message(
                to=event.verified_by.value,
                text=message,
            )

            logger.info(f"Sent verification confirmation for {event.report_id}")

        except WhatsAppAPIError as e:
            logger.error(
                f"Failed to send verification confirmation for {event.report_id}: {e}",
                exc_info=True,
            )
        except Exception as e:
            logger.error(
                f"Unexpected error sending verification confirmation: {e}",
                exc_info=True,
            )

    async def _handle_item_recovered(self, event: ItemRecovered) -> None:
        """Handle ItemRecovered event by sending confirmation.

        Args:
            event: ItemRecovered domain event
        """
        try:
            message = (
                f"🎉 Great news! Item marked as recovered!\n\n"
                f"📋 Report ID: {event.report_id}\n"
                f"📍 Recovery Location: {event.recovery_location.address or 'Location provided'}\n\n"
                f"We're glad your item was recovered!"
            )

            await self.whatsapp_client.send_text_message(
                to=event.recovered_by.value,
                text=message,
            )

            logger.info(f"Sent recovery confirmation for {event.report_id}")

        except WhatsAppAPIError as e:
            logger.error(
                f"Failed to send recovery confirmation for {event.report_id}: {e}",
                exc_info=True,
            )
        except Exception as e:
            logger.error(
                f"Unexpected error sending recovery confirmation: {e}",
                exc_info=True,
            )

    async def _handle_item_deleted(self, event: ItemDeleted) -> None:
        """Handle ItemDeleted event by sending confirmation.

        Args:
            event: ItemDeleted domain event
        """
        try:
            message = (
                f"🗑️ Report deleted successfully\n\n"
                f"📋 Report ID: {event.report_id}\n\n"
                f"Your report has been removed from our system."
            )

            await self.whatsapp_client.send_text_message(
                to=event.deleted_by.value,
                text=message,
            )

            logger.info(f"Sent deletion confirmation for {event.report_id}")

        except WhatsAppAPIError as e:
            logger.error(
                f"Failed to send deletion confirmation for {event.report_id}: {e}",
                exc_info=True,
            )
        except Exception as e:
            logger.error(
                f"Unexpected error sending deletion confirmation: {e}",
                exc_info=True,
            )

    async def _handle_item_updated(self, event: ItemUpdated) -> None:
        """Handle ItemUpdated event by sending confirmation.

        Args:
            event: ItemUpdated domain event
        """
        try:
            fields_updated = ", ".join(event.updated_fields.keys())
            message = (
                f"✏️ Report updated successfully\n\n"
                f"📋 Report ID: {event.report_id}\n"
                f"📝 Updated fields: {fields_updated}\n\n"
                f"Your changes have been saved."
            )

            await self.whatsapp_client.send_text_message(
                to=event.updated_by.value,
                text=message,
            )

            logger.info(f"Sent update confirmation for {event.report_id}")

        except WhatsAppAPIError as e:
            logger.error(
                f"Failed to send update confirmation for {event.report_id}: {e}",
                exc_info=True,
            )
        except Exception as e:
            logger.error(
                f"Unexpected error sending update confirmation: {e}",
                exc_info=True,
            )
