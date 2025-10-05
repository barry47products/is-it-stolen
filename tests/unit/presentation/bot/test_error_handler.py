"""Tests for error handler."""

import pytest

from src.domain.exceptions.domain_exceptions import (
    DomainError,
    InvalidItemCategoryError,
    InvalidLocationError,
    ItemNotFoundError,
    RepositoryError,
)
from src.infrastructure.cache.rate_limiter import RateLimitExceeded
from src.infrastructure.whatsapp.exceptions import (
    WhatsAppAPIError,
    WhatsAppError,
    WhatsAppRateLimitError,
)
from src.presentation.bot.error_handler import ErrorHandler
from src.presentation.bot.exceptions import (
    ConversationError,
    InvalidStateTransitionError,
)


@pytest.mark.unit
class TestErrorHandler:
    """Test error handler."""

    def test_handle_repository_error(self) -> None:
        """Test handling repository error."""
        # Arrange
        handler = ErrorHandler()
        error = RepositoryError("Database connection failed")

        # Act
        response = handler.handle_error(error)

        # Assert
        assert "try again" in response.lower() or "temporarily" in response.lower()
        assert "error" in response.lower() or "problem" in response.lower()

    def test_handle_invalid_location_error(self) -> None:
        """Test handling invalid location error."""
        # Arrange
        handler = ErrorHandler()
        error = InvalidLocationError("Latitude must be between -90 and 90")

        # Act
        response = handler.handle_error(error)

        # Assert
        assert "location" in response.lower()
        assert "invalid" in response.lower() or "error" in response.lower()

    def test_handle_item_not_found_error(self) -> None:
        """Test handling item not found error."""
        # Arrange
        handler = ErrorHandler()
        error = ItemNotFoundError("Item not found")

        # Act
        response = handler.handle_error(error)

        # Assert
        assert "not found" in response.lower() or "doesn't exist" in response.lower()

    def test_handle_whatsapp_api_error(self) -> None:
        """Test handling WhatsApp API error."""
        # Arrange
        handler = ErrorHandler()
        error = WhatsAppAPIError("API request failed", error_code=400)

        # Act
        response = handler.handle_error(error)

        # Assert
        assert "try again" in response.lower() or "error" in response.lower()

    def test_handle_whatsapp_rate_limit_error(self) -> None:
        """Test handling WhatsApp rate limit error."""
        # Arrange
        handler = ErrorHandler()
        error = WhatsAppRateLimitError("Too many requests")

        # Act
        response = handler.handle_error(error)

        # Assert
        assert "too many" in response.lower() or "wait" in response.lower()
        assert "try again" in response.lower() or "later" in response.lower()

    def test_handle_invalid_state_transition_error(self) -> None:
        """Test handling invalid state transition error."""
        # Arrange
        handler = ErrorHandler()
        error = InvalidStateTransitionError("IDLE", "COMPLETE")

        # Act
        response = handler.handle_error(error)

        # Assert
        assert "start over" in response.lower() or "restart" in response.lower()

    def test_handle_generic_domain_error(self) -> None:
        """Test handling generic domain error."""
        # Arrange
        handler = ErrorHandler()
        error = DomainError("Generic domain error")

        # Act
        response = handler.handle_error(error)

        # Assert
        assert "error" in response.lower() or "problem" in response.lower()

    def test_handle_unexpected_exception(self) -> None:
        """Test handling unexpected exception."""
        # Arrange
        handler = ErrorHandler()
        error = ValueError("Unexpected error")

        # Act
        response = handler.handle_error(error)

        # Assert
        assert (
            "unexpected" in response.lower()
            or "something went wrong" in response.lower()
        )
        assert "try again" in response.lower()

    def test_all_error_messages_user_friendly(self) -> None:
        """Test all error messages are user-friendly."""
        # Arrange
        handler = ErrorHandler()
        errors = [
            InvalidLocationError("Test"),
            ItemNotFoundError("Test"),
            RepositoryError("Test"),
            WhatsAppAPIError("Test"),
            ValueError("Test"),
        ]

        # Act & Assert
        for error in errors:
            response = handler.handle_error(error)
            # Should not contain technical jargon
            assert "exception" not in response.lower()
            assert "traceback" not in response.lower()
            assert "stack" not in response.lower()
            # Should be helpful
            assert len(response) > 10  # Not empty
            assert len(response) < 500  # Not too long

    def test_error_messages_provide_recovery_suggestions(self) -> None:
        """Test error messages provide recovery suggestions."""
        # Arrange
        handler = ErrorHandler()
        recovery_phrases = [
            "try again",
            "please",
            "send",
            "type",
            "start over",
            "wait",
            "later",
        ]

        errors = [
            RepositoryError("Test"),
            WhatsAppRateLimitError("Test"),
            InvalidStateTransitionError("IDLE", "COMPLETE"),
        ]

        # Act & Assert
        for error in errors:
            response = handler.handle_error(error)
            assert any(phrase in response.lower() for phrase in recovery_phrases)

    def test_handle_invalid_category_error(self) -> None:
        """Test handling invalid category error."""
        # Arrange
        handler = ErrorHandler()
        error = InvalidItemCategoryError("Unknown category")

        # Act
        response = handler.handle_error(error)

        # Assert
        assert "type" in response.lower()
        assert "recognize" in response.lower() or "invalid" in response.lower()

    def test_handle_generic_whatsapp_error(self) -> None:
        """Test handling generic WhatsApp error."""
        # Arrange
        handler = ErrorHandler()
        error = WhatsAppError("Generic WhatsApp problem")

        # Act
        response = handler.handle_error(error)

        # Assert
        assert "whatsapp" in response.lower() or "problem" in response.lower()
        assert "try again" in response.lower()

    def test_handle_generic_conversation_error(self) -> None:
        """Test handling generic conversation error (not state transition)."""
        # Arrange
        handler = ErrorHandler()
        error = ConversationError("Generic conversation problem")

        # Act
        response = handler.handle_error(error)

        # Assert
        assert "conversation" in response.lower() or "problem" in response.lower()
        assert "try" in response.lower() or "cancel" in response.lower()

    def test_handle_rate_limit_exceeded_error(self) -> None:
        """Test handling rate limit exceeded error."""
        # Arrange
        handler = ErrorHandler()
        error = RateLimitExceeded("Rate limit exceeded", retry_after=90)

        # Act
        response = handler.handle_error(error)

        # Assert
        assert "too quickly" in response.lower() or "wait" in response.lower()
        assert "1 minute" in response.lower()
        assert "30 second" in response.lower()

    def test_handle_rate_limit_exceeded_seconds_only(self) -> None:
        """Test handling rate limit with seconds only."""
        # Arrange
        handler = ErrorHandler()
        error = RateLimitExceeded("Rate limit exceeded", retry_after=45)

        # Act
        response = handler.handle_error(error)

        # Assert
        assert "45 seconds" in response.lower()
        assert "minute" not in response.lower()

    def test_handle_rate_limit_exceeded_minutes_only(self) -> None:
        """Test handling rate limit with exact minutes (no seconds)."""
        # Arrange
        handler = ErrorHandler()
        error = RateLimitExceeded("Rate limit exceeded", retry_after=120)

        # Act
        response = handler.handle_error(error)

        # Assert
        assert "2 minutes" in response.lower()
        assert "second" not in response.lower()
