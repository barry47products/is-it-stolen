"""Context management for structured logging."""

from contextvars import ContextVar
from typing import Any

# Context variable for request ID (shared across async tasks)
request_id_var: ContextVar[str | None] = ContextVar("request_id", default=None)


def set_request_id(request_id: str) -> None:
    """Set request ID in context for correlation across logs.

    Args:
        request_id: Unique request identifier (UUID)
    """
    request_id_var.set(request_id)


def get_request_id() -> str | None:
    """Get current request ID from context.

    Returns:
        Request ID if set, None otherwise
    """
    return request_id_var.get()


def clear_request_id() -> None:
    """Clear request ID from context (e.g., after request completes)."""
    request_id_var.set(None)


def add_request_id_processor(
    _logger: Any, _method_name: str, event_dict: dict[str, Any]
) -> dict[str, Any]:
    """Add request ID to log event from context.

    This is a structlog processor that automatically adds request_id
    to every log event if it's set in the context.

    Args:
        _logger: Logger instance (unused but required by structlog)
        _method_name: Method name (unused but required by structlog)
        event_dict: Event dictionary to process

    Returns:
        Event dictionary with request_id added if available
    """
    request_id = get_request_id()
    if request_id:
        event_dict["request_id"] = request_id

    return event_dict
