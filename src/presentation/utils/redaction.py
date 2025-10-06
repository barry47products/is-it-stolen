"""Utilities for redacting sensitive data from logs."""


def redact_phone_number(phone: str) -> str:
    """Redact phone number for logging, keeping only last 4 digits.

    This function sanitizes phone numbers to prevent PII leakage in logs.

    Args:
        phone: Phone number to redact

    Returns:
        Redacted phone number (e.g., "***1234")
    """
    if not phone:
        return "***"
    return f"***{phone[-4:]}" if len(phone) > 4 else "***"
