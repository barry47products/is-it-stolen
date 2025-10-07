"""Tests for webhook receiver."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from src.infrastructure.config.settings import Settings
from src.presentation.api.v1.webhook_receiver import _process_single_message
from src.presentation.bot.message_processor import MessageProcessor


@pytest.mark.unit
class TestWebhookReceiverInteractiveMessages:
    """Test webhook receiver handling of interactive messages."""

    @pytest.mark.asyncio
    async def test_extracts_button_id_from_interactive_message(self) -> None:
        """Test that button_id is extracted as message_text for interactive messages."""
        # Arrange
        msg = {
            "from": "+1234567890",
            "message_id": "wamid.test123",
            "type": "interactive",
            "button_id": "check_item",
            "button_title": "Check Item",
        }

        # Mock message processor
        message_processor = MagicMock(spec=MessageProcessor)
        message_processor.process_message = AsyncMock(
            return_value={"reply": "Processing...", "state": "checking_category"}
        )

        # Mock settings
        settings = MagicMock(spec=Settings)
        settings.environment = "production"

        # Act
        success, message_text = await _process_single_message(
            msg, message_processor, settings
        )

        # Assert
        assert success is True
        assert message_text == "check_item"
        message_processor.process_message.assert_called_once_with(
            "+1234567890", "check_item"
        )

    @pytest.mark.asyncio
    async def test_extracts_list_id_from_interactive_message(self) -> None:
        """Test that list_id is extracted as message_text for interactive list messages."""
        # Arrange
        msg = {
            "from": "+1234567890",
            "message_id": "wamid.test456",
            "type": "interactive",
            "list_id": "bicycle",
            "list_title": "Bicycle",
            "list_description": "Two-wheeled vehicle",
        }

        # Mock message processor
        message_processor = MagicMock(spec=MessageProcessor)
        message_processor.process_message = AsyncMock(
            return_value={"reply": "Great choice!", "state": "checking_description"}
        )

        # Mock settings
        settings = MagicMock(spec=Settings)
        settings.environment = "production"

        # Act
        success, message_text = await _process_single_message(
            msg, message_processor, settings
        )

        # Assert
        assert success is True
        assert message_text == "bicycle"
        message_processor.process_message.assert_called_once_with(
            "+1234567890", "bicycle"
        )

    @pytest.mark.asyncio
    async def test_button_id_takes_precedence_over_list_id(self) -> None:
        """Test that button_id takes precedence when both button_id and list_id present."""
        # Arrange
        msg = {
            "from": "+1234567890",
            "message_id": "wamid.test789",
            "type": "interactive",
            "button_id": "check_item",
            "list_id": "bicycle",  # Should be ignored
        }

        # Mock message processor
        message_processor = MagicMock(spec=MessageProcessor)
        message_processor.process_message = AsyncMock(
            return_value={"reply": "OK", "state": "main_menu"}
        )

        # Mock settings
        settings = MagicMock(spec=Settings)
        settings.environment = "production"

        # Act
        success, message_text = await _process_single_message(
            msg, message_processor, settings
        )

        # Assert
        assert success is True
        assert message_text == "check_item"  # button_id, not list_id
