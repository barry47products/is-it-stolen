"""Custom structlog processors for filtering and transforming log data."""

import hashlib
from typing import Any

# Sensitive field patterns to redact from logs (reused from Sentry integration)
SENSITIVE_KEYS = {
    "password",
    "passwd",
    "pwd",
    "token",
    "secret",
    "api",
    "key",
    "access",
    "refresh",
    "auth",
    "authorization",
    "cookie",
    "session",
    "csrf",
    "ssn",
    "credit",
    "card",
    "cvv",
    "pin",
}


def filter_sensitive_data(
    _logger: Any, _method_name: str, event_dict: dict[str, Any]
) -> dict[str, Any]:
    """Filter sensitive data from log records.

    Args:
        _logger: Logger instance (unused but required by structlog)
        _method_name: Method name (unused but required by structlog)
        event_dict: Event dictionary to process

    Returns:
        Filtered event dictionary with sensitive data redacted
    """
    return _filter_dict(event_dict)


def _filter_dict(data: dict[str, Any]) -> dict[str, Any]:
    """Recursively filter sensitive keys from dictionary.

    Args:
        data: Dictionary to filter

    Returns:
        Filtered dictionary with sensitive values redacted
    """
    filtered: dict[str, Any] = {}

    for key, value in data.items():
        key_lower = key.lower()

        # Check if key contains sensitive patterns
        is_sensitive = any(sensitive in key_lower for sensitive in SENSITIVE_KEYS)

        if is_sensitive:
            filtered[key] = "[REDACTED]"
        elif isinstance(value, dict):
            filtered[key] = _filter_dict(value)
        elif isinstance(value, list):
            filtered[key] = [
                _filter_dict(item) if isinstance(item, dict) else item for item in value
            ]
        else:
            filtered[key] = value

    return filtered


def hash_phone_number(phone: str) -> str:
    """Hash phone number for privacy-compliant correlation.

    Uses SHA256 and returns first 8 characters for log correlation
    while maintaining user privacy.

    Args:
        phone: Phone number to hash (e.g., +447700900000)

    Returns:
        First 8 characters of SHA256 hash (e.g., "a1b2c3d4")
    """
    return hashlib.sha256(phone.encode()).hexdigest()[:8]


def add_hashed_phone(
    _logger: Any, _method_name: str, event_dict: dict[str, Any]
) -> dict[str, Any]:
    """Add hashed phone number to event if phone is present.

    Args:
        _logger: Logger instance (unused but required by structlog)
        _method_name: Method name (unused but required by structlog)
        event_dict: Event dictionary to process

    Returns:
        Event dictionary with user_id_hash added if phone was present
    """
    phone = event_dict.get("phone")
    if phone:
        event_dict["user_id_hash"] = hash_phone_number(phone)
        # Remove the original phone for privacy
        del event_dict["phone"]

    return event_dict
