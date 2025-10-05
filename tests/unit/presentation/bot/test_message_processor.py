"""Tests for message processor."""

from unittest.mock import AsyncMock, MagicMock

import pytest

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
