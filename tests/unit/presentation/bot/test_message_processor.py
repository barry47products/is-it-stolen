"""Tests for message processor."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from src.presentation.bot.context import ConversationContext
from src.presentation.bot.message_processor import MessageProcessor
from src.presentation.bot.states import ConversationState


@pytest.mark.unit
class TestMessageProcessor:
    """Test message processor."""

    @pytest.mark.asyncio
    async def test_process_message_creates_context(self) -> None:
        """Test process_message creates or retrieves context."""
        # Arrange
        phone_number = "+1234567890"
        message_text = "Hello"

        state_machine = MagicMock()
        state_machine.get_or_create = AsyncMock(
            return_value=ConversationContext(
                phone_number=phone_number,
                state=ConversationState.IDLE,
            )
        )

        processor = MessageProcessor(state_machine=state_machine)

        # Act
        response = await processor.process_message(phone_number, message_text)

        # Assert
        state_machine.get_or_create.assert_called_once_with(phone_number)
        assert "reply" in response
        assert "state" in response
        assert response["state"] == "idle"

    @pytest.mark.asyncio
    async def test_process_message_returns_acknowledgment(self) -> None:
        """Test process_message returns acknowledgment."""
        # Arrange
        phone_number = "+1234567890"
        message_text = "Test message"

        state_machine = MagicMock()
        state_machine.get_or_create = AsyncMock(
            return_value=ConversationContext(
                phone_number=phone_number,
                state=ConversationState.MAIN_MENU,
            )
        )

        processor = MessageProcessor(state_machine=state_machine)

        # Act
        response = await processor.process_message(phone_number, message_text)

        # Assert
        assert f"Received: {message_text}" in response["reply"]
        assert response["state"] == "main_menu"
