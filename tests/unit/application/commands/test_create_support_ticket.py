"""Tests for CreateSupportTicketHandler."""

import pytest

from src.application.commands.create_support_ticket import (
    CreateSupportTicketHandler,
)


class TestCreateSupportTicketHandler:
    """Test cases for CreateSupportTicketHandler."""

    @pytest.mark.asyncio
    async def test_creates_ticket_with_valid_message(self) -> None:
        """Test that handler creates ticket with valid message."""
        # Arrange
        handler = CreateSupportTicketHandler()
        data = {"message": "I need help with my account"}

        # Act
        result = await handler.handle(data)

        # Assert
        assert result["ticket_id"] is not None
        assert result["message"] == "Your support ticket has been created successfully!"
        assert result["email"] is None

    @pytest.mark.asyncio
    async def test_creates_ticket_with_email(self) -> None:
        """Test that handler creates ticket with optional email."""
        # Arrange
        handler = CreateSupportTicketHandler()
        data = {
            "message": "I need help with my account",
            "email": "user@example.com",
        }

        # Act
        result = await handler.handle(data)

        # Assert
        assert result["ticket_id"] is not None
        assert result["email"] == "user@example.com"

    @pytest.mark.asyncio
    async def test_skips_email_when_user_types_skip(self) -> None:
        """Test that handler skips email when user types 'skip'."""
        # Arrange
        handler = CreateSupportTicketHandler()
        data = {"message": "I need help with my account", "email": "skip"}

        # Act
        result = await handler.handle(data)

        # Assert
        assert result["email"] is None

    @pytest.mark.asyncio
    async def test_raises_error_for_empty_message(self) -> None:
        """Test that handler raises error for empty message."""
        # Arrange
        handler = CreateSupportTicketHandler()
        data = {"message": ""}

        # Act & Assert
        with pytest.raises(ValueError, match="Message cannot be empty"):
            await handler.handle(data)

    @pytest.mark.asyncio
    async def test_raises_error_for_whitespace_message(self) -> None:
        """Test that handler raises error for whitespace-only message."""
        # Arrange
        handler = CreateSupportTicketHandler()
        data = {"message": "   "}

        # Act & Assert
        with pytest.raises(ValueError, match="Message cannot be empty"):
            await handler.handle(data)

    @pytest.mark.asyncio
    async def test_handles_missing_email_gracefully(self) -> None:
        """Test that handler handles missing email field gracefully."""
        # Arrange
        handler = CreateSupportTicketHandler()
        data = {"message": "I need help"}

        # Act
        result = await handler.handle(data)

        # Assert
        assert result["email"] is None
