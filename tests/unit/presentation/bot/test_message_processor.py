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
