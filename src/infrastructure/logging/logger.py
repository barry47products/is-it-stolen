"""Logger utilities for structured logging."""

from typing import Any

import structlog

from src.infrastructure.logging.processors import hash_phone_number


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:  # type: ignore[no-any-unimported]
    """Get a configured structured logger.

    Args:
        name: Logger name (usually __name__ of the module).
              If None, returns root logger.

    Returns:
        Configured structlog logger instance

    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("User logged in", user_id_hash="a1b2c3d4")
    """
    return structlog.get_logger(name)


def bind_user(phone: str, **extra: Any) -> dict[str, Any]:
    """Create binding context for user-related logs.

    Hashes phone number for privacy-compliant correlation.

    Args:
        phone: User's phone number (e.g., +447700900000)
        **extra: Additional context to bind

    Returns:
        Dictionary of context to bind to logger

    Example:
        >>> logger = get_logger(__name__)
        >>> logger = logger.bind(**bind_user("+447700900000", action="report"))
        >>> logger.info("Item reported")  # Will include user_id_hash and action
    """
    context = {
        "user_id_hash": hash_phone_number(phone),
        **extra,
    }
    return context


def bind_report(report_id: str, **extra: Any) -> dict[str, Any]:
    """Create binding context for report-related logs.

    Args:
        report_id: Report/item UUID
        **extra: Additional context to bind

    Returns:
        Dictionary of context to bind to logger

    Example:
        >>> logger = get_logger(__name__)
        >>> logger = logger.bind(**bind_report("uuid-here", category="bicycle"))
        >>> logger.info("Item verified")  # Will include report_id and category
    """
    context = {
        "report_id": report_id,
        **extra,
    }
    return context
