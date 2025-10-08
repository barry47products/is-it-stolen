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
from src.presentation.bot.messages import ERROR_MESSAGES

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
        return ERROR_MESSAGES.repository_error

    def _handle_invalid_location_error(self, _error: InvalidLocationError) -> str:
        """Handle invalid location errors."""
        return ERROR_MESSAGES.invalid_location

    def _handle_invalid_category_error(self, _error: InvalidItemCategoryError) -> str:
        """Handle invalid category errors."""
        return ERROR_MESSAGES.invalid_category

    def _handle_item_not_found_error(self, _error: ItemNotFoundError) -> str:
        """Handle item not found errors."""
        return ERROR_MESSAGES.item_not_found

    def _handle_rate_limit_error(self, _error: WhatsAppRateLimitError) -> str:
        """Handle rate limit errors."""
        return ERROR_MESSAGES.rate_limit_exceeded

    def _handle_whatsapp_api_error(self, _error: WhatsAppAPIError) -> str:
        """Handle WhatsApp API errors."""
        return ERROR_MESSAGES.whatsapp_api_error

    def _handle_whatsapp_error(self, _error: WhatsAppError) -> str:
        """Handle generic WhatsApp errors."""
        return ERROR_MESSAGES.whatsapp_error

    def _handle_invalid_state_transition_error(
        self, _error: InvalidStateTransitionError
    ) -> str:
        """Handle invalid state transition errors."""
        return ERROR_MESSAGES.invalid_state_transition

    def _handle_conversation_error(self, _error: ConversationError) -> str:
        """Handle generic conversation errors."""
        return ERROR_MESSAGES.conversation_error

    def _handle_domain_error(self, _error: DomainError) -> str:
        """Handle generic domain errors."""
        return ERROR_MESSAGES.domain_error

    def _handle_rate_limit_exceeded_error(self, error: RateLimitExceeded) -> str:
        """Handle rate limit exceeded errors."""
        retry_minutes = error.retry_after // 60 if error.retry_after >= 60 else 0
        retry_seconds = error.retry_after % 60

        return ERROR_MESSAGES.rate_limit_with_time(retry_minutes, retry_seconds)

    def _handle_unexpected_error(self, _error: Exception) -> str:
        """Handle unexpected errors."""
        return ERROR_MESSAGES.unexpected_error
