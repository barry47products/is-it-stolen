"""Tests for message processor."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from src.infrastructure.cache.rate_limiter import RateLimitExceeded
from src.presentation.bot.message_processor import MessageProcessor


@pytest.mark.unit
class TestMessageProcessor:
    """Test message processor."""

    @pytest.mark.asyncio
    async def test_process_message_routes_and_sends_response(self) -> None:
        """Test process_message routes message and sends WhatsApp response."""
        # Arrange
        phone_number = "+1234567890"
        message_text = "Hello"

        # Mock router
        router = MagicMock()
        router.route_message = AsyncMock(
            return_value={"reply": "Welcome!", "state": "main_menu"}
        )

        # Mock WhatsApp client
        whatsapp_client = MagicMock()
        whatsapp_client.send_text_message = AsyncMock()

        # Mock state machine
        state_machine = MagicMock()

        processor = MessageProcessor(
            state_machine=state_machine, whatsapp_client=whatsapp_client
        )
        processor.router = router  # Replace router with our mock

        # Act
        response = await processor.process_message(phone_number, message_text)

        # Assert
        router.route_message.assert_called_once_with(phone_number, message_text)
        whatsapp_client.send_text_message.assert_called_once_with(
            to=phone_number, text="Welcome!"
        )
        assert response["reply"] == "Welcome!"
        assert response["state"] == "main_menu"

    @pytest.mark.asyncio
    async def test_process_message_checks_rate_limit_when_limiter_provided(
        self,
    ) -> None:
        """Test process_message checks rate limit when limiter is provided."""
        # Arrange
        phone_number = "+1234567890"
        message_text = "Hello"

        # Mock rate limiter
        rate_limiter = MagicMock()
        rate_limiter.check_rate_limit = AsyncMock()

        # Mock router
        router = MagicMock()
        router.route_message = AsyncMock(
            return_value={"reply": "Welcome!", "state": "main_menu"}
        )

        # Mock WhatsApp client
        whatsapp_client = MagicMock()
        whatsapp_client.send_text_message = AsyncMock()

        # Mock state machine
        state_machine = MagicMock()

        processor = MessageProcessor(
            state_machine=state_machine,
            whatsapp_client=whatsapp_client,
            rate_limiter=rate_limiter,
        )
        processor.router = router

        # Act
        await processor.process_message(phone_number, message_text)

        # Assert
        rate_limiter.check_rate_limit.assert_called_once_with(phone_number)

    @pytest.mark.asyncio
    async def test_process_message_handles_rate_limit_exceeded(self) -> None:
        """Test process_message handles RateLimitExceeded error."""
        # Arrange
        phone_number = "+1234567890"
        message_text = "Hello"

        # Mock rate limiter that raises RateLimitExceeded
        rate_limiter = MagicMock()
        rate_limiter.check_rate_limit = AsyncMock(
            side_effect=RateLimitExceeded("Rate limit exceeded", retry_after=60)
        )

        # Mock router (should not be called)
        router = MagicMock()
        router.route_message = AsyncMock()

        # Mock WhatsApp client
        whatsapp_client = MagicMock()
        whatsapp_client.send_text_message = AsyncMock()

        # Mock state machine
        state_machine = MagicMock()

        processor = MessageProcessor(
            state_machine=state_machine,
            whatsapp_client=whatsapp_client,
            rate_limiter=rate_limiter,
        )
        processor.router = router

        # Act
        response = await processor.process_message(phone_number, message_text)

        # Assert
        rate_limiter.check_rate_limit.assert_called_once_with(phone_number)
        router.route_message.assert_not_called()
        whatsapp_client.send_text_message.assert_called_once()
        assert "too quickly" in response["reply"].lower()
        assert response["state"] == "rate_limited"

    @pytest.mark.asyncio
    async def test_process_message_skips_rate_limit_when_no_limiter(self) -> None:
        """Test process_message skips rate limiting when no limiter provided."""
        # Arrange
        phone_number = "+1234567890"
        message_text = "Hello"

        # Mock router
        router = MagicMock()
        router.route_message = AsyncMock(
            return_value={"reply": "Welcome!", "state": "main_menu"}
        )

        # Mock WhatsApp client
        whatsapp_client = MagicMock()
        whatsapp_client.send_text_message = AsyncMock()

        # Mock state machine
        state_machine = MagicMock()

        # Create processor WITHOUT rate_limiter
        processor = MessageProcessor(
            state_machine=state_machine,
            whatsapp_client=whatsapp_client,
            rate_limiter=None,
        )
        processor.router = router

        # Act
        response = await processor.process_message(phone_number, message_text)

        # Assert
        router.route_message.assert_called_once_with(phone_number, message_text)
        assert response["reply"] == "Welcome!"
        assert response["state"] == "main_menu"

    @pytest.mark.asyncio
    async def test_process_message_sends_interactive_reply_buttons(self) -> None:
        """Test process_message sends interactive reply buttons."""
        # Arrange
        phone_number = "+1234567890"
        message_text = "Hi"

        # Mock router returns interactive button payload
        interactive_payload = {
            "type": "interactive",
            "interactive": {
                "type": "button",
                "body": {"text": "Welcome! Choose an option:"},
                "action": {
                    "buttons": [
                        {
                            "type": "reply",
                            "reply": {"id": "check_item", "title": "Check Item"},
                        },
                        {
                            "type": "reply",
                            "reply": {"id": "report_item", "title": "Report Item"},
                        },
                    ]
                },
            },
        }

        router = MagicMock()
        router.route_message = AsyncMock(
            return_value={"reply": interactive_payload, "state": "main_menu"}
        )

        # Mock WhatsApp client
        whatsapp_client = MagicMock()
        whatsapp_client.send_reply_buttons = AsyncMock()

        # Mock state machine
        state_machine = MagicMock()

        processor = MessageProcessor(
            state_machine=state_machine, whatsapp_client=whatsapp_client
        )
        processor.router = router

        # Act
        response = await processor.process_message(phone_number, message_text)

        # Assert
        whatsapp_client.send_reply_buttons.assert_called_once_with(
            to=phone_number,
            body="Welcome! Choose an option:",
            buttons=[
                {"id": "check_item", "title": "Check Item"},
                {"id": "report_item", "title": "Report Item"},
            ],
        )
        # Response should have text version for backward compatibility
        assert response["reply"] == "Welcome! Choose an option:"
        assert response["state"] == "main_menu"

    @pytest.mark.asyncio
    async def test_process_message_sends_interactive_list_message(self) -> None:
        """Test process_message sends interactive list message."""
        # Arrange
        phone_number = "+1234567890"
        message_text = "bicycle"

        # Mock router returns interactive list payload
        interactive_payload = {
            "type": "interactive",
            "interactive": {
                "type": "list",
                "header": {"type": "text", "text": "Choose Category"},
                "body": {"text": "What type of item?"},
                "action": {
                    "button": "Select Category",
                    "sections": [
                        {
                            "title": "Common Items",
                            "rows": [
                                {
                                    "id": "bicycle",
                                    "title": "Bicycle",
                                    "description": "Bikes",
                                },
                                {
                                    "id": "phone",
                                    "title": "Phone",
                                    "description": "Phones",
                                },
                            ],
                        }
                    ],
                },
            },
        }

        router = MagicMock()
        router.route_message = AsyncMock(
            return_value={"reply": interactive_payload, "state": "checking_category"}
        )

        # Mock WhatsApp client
        whatsapp_client = MagicMock()
        whatsapp_client.send_list_message = AsyncMock()

        # Mock state machine
        state_machine = MagicMock()

        processor = MessageProcessor(
            state_machine=state_machine, whatsapp_client=whatsapp_client
        )
        processor.router = router

        # Act
        response = await processor.process_message(phone_number, message_text)

        # Assert
        whatsapp_client.send_list_message.assert_called_once_with(
            to=phone_number,
            body="What type of item?",
            button_text="Select Category",
            sections=[
                {
                    "title": "Common Items",
                    "rows": [
                        {"id": "bicycle", "title": "Bicycle", "description": "Bikes"},
                        {"id": "phone", "title": "Phone", "description": "Phones"},
                    ],
                }
            ],
            header="Choose Category",
        )
        # Response should have text version for backward compatibility
        assert response["reply"] == "What type of item?"
        assert response["state"] == "checking_category"

    @pytest.mark.asyncio
    async def test_process_message_handles_dict_reply_without_interactive_type(
        self,
    ) -> None:
        """Test process_message handles dict reply that is not interactive type."""
        # Arrange
        phone_number = "+1234567890"
        message_text = "test"

        # Mock router returns a dict but not interactive type (edge case)
        non_interactive_dict = {"type": "something_else", "data": "test"}

        router = MagicMock()
        router.route_message = AsyncMock(
            return_value={"reply": non_interactive_dict, "state": "idle"}
        )

        # Mock WhatsApp client
        whatsapp_client = MagicMock()
        whatsapp_client.send_text_message = AsyncMock()

        # Mock state machine
        state_machine = MagicMock()

        processor = MessageProcessor(
            state_machine=state_machine, whatsapp_client=whatsapp_client
        )
        processor.router = router

        # Act
        response = await processor.process_message(phone_number, message_text)

        # Assert
        # Should not call any WhatsApp send methods since it's not a known type
        whatsapp_client.send_reply_buttons.assert_not_called()
        whatsapp_client.send_list_message.assert_not_called()
        whatsapp_client.send_text_message.assert_not_called()
        # Reply text should be empty since we couldn't extract anything
        assert response["reply"] == ""
        assert response["state"] == "idle"

    @pytest.mark.asyncio
    async def test_process_message_handles_unknown_interactive_type(self) -> None:
        """Test process_message handles unknown interactive message type."""
        # Arrange
        phone_number = "+1234567890"
        message_text = "test"

        # Mock router returns interactive message with unknown type (future-proofing)
        unknown_interactive = {
            "type": "interactive",
            "interactive": {
                "type": "future_new_type",  # Unknown type
                "body": {"text": "Future message"},
                "action": {"some_future_field": "value"},
            },
        }

        router = MagicMock()
        router.route_message = AsyncMock(
            return_value={"reply": unknown_interactive, "state": "main_menu"}
        )

        # Mock WhatsApp client
        whatsapp_client = MagicMock()
        whatsapp_client.send_reply_buttons = AsyncMock()
        whatsapp_client.send_list_message = AsyncMock()
        whatsapp_client.send_text_message = AsyncMock()

        # Mock state machine
        state_machine = MagicMock()

        processor = MessageProcessor(
            state_machine=state_machine, whatsapp_client=whatsapp_client
        )
        processor.router = router

        # Act
        response = await processor.process_message(phone_number, message_text)

        # Assert
        # Should not call any send methods for unknown type
        whatsapp_client.send_reply_buttons.assert_not_called()
        whatsapp_client.send_list_message.assert_not_called()
        whatsapp_client.send_text_message.assert_not_called()
        # Reply text should be empty since type is unknown
        assert response["reply"] == ""
        assert response["state"] == "main_menu"
