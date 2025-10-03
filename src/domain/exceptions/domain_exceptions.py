"""Domain-specific exception types."""


class DomainError(Exception):
    """Base exception for all domain errors.

    All domain-specific exceptions should extend this class to enable
    consistent error handling across layers.
    """

    def __init__(self, message: str, code: str = "DOMAIN_ERROR") -> None:
        """Initialize domain error with message and error code.

        Args:
            message: Human-readable error description
            code: Error code for client handling
        """
        super().__init__(message)
        self.code = code


class InvalidLocationError(DomainError):
    """Raised when location coordinates are invalid.

    Examples:
        - Latitude outside -90 to 90 range
        - Longitude outside -180 to 180 range
        - Invalid coordinate format
    """

    def __init__(self, message: str) -> None:
        """Initialize with location validation error message."""
        super().__init__(message, code="INVALID_LOCATION")


class InvalidPhoneNumberError(DomainError):
    """Raised when phone number validation fails.

    Examples:
        - Missing country code prefix
        - Invalid E.164 format
        - Invalid phone number structure
    """

    def __init__(self, message: str) -> None:
        """Initialize with phone number validation error message."""
        super().__init__(message, code="INVALID_PHONE_NUMBER")


class InvalidItemCategoryError(DomainError):
    """Raised when item category is unknown or invalid.

    Examples:
        - Unknown category name
        - Unrecognized keyword
        - Invalid enum value
    """

    def __init__(self, message: str) -> None:
        """Initialize with item category validation error message."""
        super().__init__(message, code="INVALID_ITEM_CATEGORY")


class ItemNotFoundError(DomainError):
    """Raised when a stolen item cannot be found.

    Examples:
        - Item with given ID doesn't exist
        - Item has been deleted
        - Invalid item reference
    """

    def __init__(self, message: str) -> None:
        """Initialize with item not found error message."""
        super().__init__(message, code="ITEM_NOT_FOUND")


class ItemAlreadyRecoveredError(DomainError):
    """Raised when attempting to recover an already recovered item.

    This is a business rule violation - items can only be recovered once.
    """

    def __init__(self, message: str) -> None:
        """Initialize with item already recovered error message."""
        super().__init__(message, code="ITEM_ALREADY_RECOVERED")


class ItemNotActiveError(DomainError):
    """Raised when attempting to verify a non-active item.

    Only active items can be verified. Recovered or expired items cannot.
    """

    def __init__(self, message: str) -> None:
        """Initialize with item not active error message."""
        super().__init__(message, code="ITEM_NOT_ACTIVE")


class ItemAlreadyVerifiedError(DomainError):
    """Raised when attempting to verify an already verified item.

    This is a business rule violation - items can only be verified once.
    """

    def __init__(self, message: str) -> None:
        """Initialize with item already verified error message."""
        super().__init__(message, code="ITEM_ALREADY_VERIFIED")


class InvalidPoliceReferenceError(DomainError):
    """Raised when police reference validation fails.

    Examples:
        - Invalid reference format
        - Missing required components
        - Invalid reference structure
    """

    def __init__(self, message: str) -> None:
        """Initialize with police reference validation error message."""
        super().__init__(message, code="INVALID_POLICE_REFERENCE")


class UnauthorizedVerificationError(DomainError):
    """Raised when user is not authorized to verify an item.

    Only the original reporter can verify their own report.
    """

    def __init__(self, message: str) -> None:
        """Initialize with unauthorized verification error message."""
        super().__init__(message, code="UNAUTHORIZED_VERIFICATION")


class ItemAlreadyDeletedException(DomainError):
    """Raised when attempting to delete an already deleted item.

    Prevents double deletion and ensures proper error handling.
    """

    def __init__(self, message: str) -> None:
        """Initialize with item already deleted error message."""
        super().__init__(message, code="ITEM_ALREADY_DELETED")


class UnauthorizedDeletionError(DomainError):
    """Raised when user is not authorized to delete an item.

    Only the original reporter can delete their own report.
    """

    def __init__(self, message: str) -> None:
        """Initialize with unauthorized deletion error message."""
        super().__init__(message, code="UNAUTHORIZED_DELETION")


class RepositoryError(DomainError):
    """Raised when repository operations fail.

    Examples:
        - Database connection fails
        - Query execution fails
        - Data persistence fails
        - Transaction rollback occurs
    """

    def __init__(self, message: str, cause: Exception | None = None) -> None:
        """Initialize with repository error message and optional cause.

        Args:
            message: Human-readable error description
            cause: Optional underlying exception that caused this error
        """
        super().__init__(message, code="REPOSITORY_ERROR")
        self.cause = cause
