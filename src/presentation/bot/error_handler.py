"""Error handler for mapping exceptions to user-friendly messages."""

import logging

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
from src.presentation.bot.exceptions import (
    ConversationError,
    InvalidStateTransitionError,
)

logger = logging.getLogger(__name__)


class ErrorHandler:
    """Handles exceptions and converts them to user-friendly messages."""

    def handle_error(self, error: Exception) -> str:
        """Convert exception to user-friendly error message.

        Args:
            error: The exception to handle

        Returns:
            User-friendly error message with recovery suggestions
        """
        # Log the error with full context
        logger.error(
            f"Error occurred: {type(error).__name__}: {error!s}",
            exc_info=True,
            extra={"error_type": type(error).__name__},
        )

        # Map specific exceptions to user-friendly messages
        if isinstance(error, RateLimitExceeded):
            return self._handle_rate_limit_exceeded_error(error)
        elif isinstance(error, RepositoryError):
            return self._handle_repository_error(error)
        elif isinstance(error, InvalidLocationError):
            return self._handle_invalid_location_error(error)
        elif isinstance(error, InvalidItemCategoryError):
            return self._handle_invalid_category_error(error)
        elif isinstance(error, ItemNotFoundError):
            return self._handle_item_not_found_error(error)
        elif isinstance(error, WhatsAppRateLimitError):
            return self._handle_rate_limit_error(error)
        elif isinstance(error, WhatsAppAPIError):
            return self._handle_whatsapp_api_error(error)
        elif isinstance(error, WhatsAppError):
            return self._handle_whatsapp_error(error)
        elif isinstance(error, InvalidStateTransitionError):
            return self._handle_invalid_state_transition_error(error)
        elif isinstance(error, ConversationError):
            return self._handle_conversation_error(error)
        elif isinstance(error, DomainError):
            return self._handle_domain_error(error)
        else:
            return self._handle_unexpected_error(error)

    def _handle_repository_error(self, _error: RepositoryError) -> str:
        """Handle repository/database errors."""
        return (
            "⚠️ We're experiencing a temporary problem.\n\n"
            "Please try again in a few moments.\n"
            "If the problem persists, please contact support."
        )

    def _handle_invalid_location_error(self, _error: InvalidLocationError) -> str:
        """Handle invalid location errors."""
        return (
            "❌ The location you provided is invalid.\n\n"
            "Please provide a valid location or type 'skip' to continue without location."
        )

    def _handle_invalid_category_error(self, _error: InvalidItemCategoryError) -> str:
        """Handle invalid category errors."""
        return (
            "❌ I didn't recognize that item type.\n\n"
            "Please try again with: bike, phone, laptop, or car"
        )

    def _handle_item_not_found_error(self, _error: ItemNotFoundError) -> str:
        """Handle item not found errors."""
        return (
            "❌ The item you're looking for doesn't exist.\n\n"
            "It may have been deleted or the ID is incorrect."
        )

    def _handle_rate_limit_error(self, _error: WhatsAppRateLimitError) -> str:
        """Handle rate limit errors."""
        return (
            "⏳ You're sending messages too quickly.\n\n"
            "Please wait a moment and try again."
        )

    def _handle_whatsapp_api_error(self, _error: WhatsAppAPIError) -> str:
        """Handle WhatsApp API errors."""
        return (
            "⚠️ We're having trouble sending your message.\n\n"
            "Please try again in a moment."
        )

    def _handle_whatsapp_error(self, _error: WhatsAppError) -> str:
        """Handle generic WhatsApp errors."""
        return "⚠️ There was a problem with WhatsApp.\n\nPlease try again shortly."

    def _handle_invalid_state_transition_error(
        self, _error: InvalidStateTransitionError
    ) -> str:
        """Handle invalid state transition errors."""
        return (
            "⚠️ Something went wrong with the conversation flow.\n\n"
            "Let's start over. Send any message to begin again."
        )

    def _handle_conversation_error(self, _error: ConversationError) -> str:
        """Handle generic conversation errors."""
        return (
            "⚠️ There was a problem with the conversation.\n\n"
            "Please try sending your message again, or type 'cancel' to start over."
        )

    def _handle_domain_error(self, _error: DomainError) -> str:
        """Handle generic domain errors."""
        return (
            "❌ There was a problem processing your request.\n\n"
            "Please try again or type 'cancel' to start over."
        )

    def _handle_rate_limit_exceeded_error(self, error: RateLimitExceeded) -> str:
        """Handle rate limit exceeded errors."""
        retry_minutes = error.retry_after // 60 if error.retry_after >= 60 else 0
        retry_seconds = error.retry_after % 60

        if retry_minutes > 0:
            retry_msg = f"{retry_minutes} minute{'s' if retry_minutes != 1 else ''}"
            if retry_seconds > 0:
                retry_msg += (
                    f" and {retry_seconds} second{'s' if retry_seconds != 1 else ''}"
                )
        else:
            retry_msg = f"{retry_seconds} second{'s' if retry_seconds != 1 else ''}"

        return (
            f"⏳ You're sending messages too quickly.\n\n"
            f"Please wait {retry_msg} before trying again.\n"
            f"This helps us keep the service running smoothly for everyone."
        )

    def _handle_unexpected_error(self, _error: Exception) -> str:
        """Handle unexpected errors."""
        return (
            "❌ Something unexpected went wrong.\n\n"
            "Please try again. If the problem persists, contact support."
        )
