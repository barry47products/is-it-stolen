"""WhatsApp API exceptions."""


class WhatsAppError(Exception):
    """Base exception for WhatsApp-related errors."""

    pass


class WhatsAppAPIError(WhatsAppError):
    """Raised when WhatsApp API returns an error response."""

    def __init__(self, message: str, error_code: int | None = None) -> None:
        """Initialize WhatsApp API error.

        Args:
            message: Error message from API
            error_code: Error code from API
        """
        super().__init__(message)
        self.error_code = error_code


class WhatsAppRateLimitError(WhatsAppError):
    """Raised when WhatsApp API rate limit is exceeded."""

    pass


class WhatsAppMediaError(WhatsAppError):
    """Raised when media download or upload fails."""

    pass
