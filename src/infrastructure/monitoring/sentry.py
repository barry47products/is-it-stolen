"""Sentry error tracking integration."""

import logging
from typing import Any, Literal, cast

import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.logging import LoggingIntegration
from sentry_sdk.integrations.redis import RedisIntegration
from sentry_sdk.types import Event, Hint  # type: ignore[import-untyped]

from src.infrastructure.config.settings import Settings

logger = logging.getLogger(__name__)

# Sensitive field patterns to scrub from error reports
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


def before_send(event: Event, _hint: Hint) -> Event | None:  # type: ignore[no-any-unimported]
    """Filter sensitive data before sending to Sentry.

    Args:
        event: Sentry event dictionary
        _hint: Additional context about the event (unused but required by Sentry)

    Returns:
        Modified event or None to drop the event
    """
    # Scrub request data
    if "request" in event:
        request = event["request"]

        # Scrub headers
        if "headers" in request:
            request["headers"] = _scrub_dict(cast("dict[str, Any]", request["headers"]))

        # Scrub query parameters
        if "query_string" in request:
            request["query_string"] = _scrub_sensitive_params(
                cast("str", request["query_string"])
            )

        # Scrub cookies
        if "cookies" in request:
            request["cookies"] = _scrub_dict(cast("dict[str, Any]", request["cookies"]))

        # Scrub POST data
        if "data" in request and isinstance(request["data"], dict):
            request["data"] = _scrub_dict(cast("dict[str, Any]", request["data"]))

    # Scrub extra data
    if "extra" in event:
        event["extra"] = _scrub_dict(cast("dict[str, Any]", event["extra"]))

    # Scrub context
    if "contexts" in event:
        event["contexts"] = _scrub_dict(cast("dict[str, Any]", event["contexts"]))

    return event


def _scrub_dict(data: dict[str, Any]) -> dict[str, Any]:
    """Scrub sensitive keys from dictionary.

    Args:
        data: Dictionary to scrub

    Returns:
        Scrubbed dictionary
    """
    scrubbed: dict[str, Any] = {}
    for key, value in data.items():
        key_lower = key.lower()

        # Check if key is sensitive
        is_sensitive = any(sensitive in key_lower for sensitive in SENSITIVE_KEYS)

        if is_sensitive:
            scrubbed[key] = "[Filtered]"
        elif isinstance(value, dict):
            scrubbed[key] = _scrub_dict(value)
        elif isinstance(value, list):
            scrubbed[key] = [
                _scrub_dict(item) if isinstance(item, dict) else item for item in value
            ]
        else:
            scrubbed[key] = value

    return scrubbed


def _scrub_sensitive_params(query_string: str) -> str:
    """Scrub sensitive parameters from query string.

    Args:
        query_string: URL query string

    Returns:
        Scrubbed query string
    """
    if not query_string:
        return query_string

    params = []
    for param in query_string.split("&"):
        if "=" in param:
            key, _value = param.split("=", 1)
            key_lower = key.lower()

            # Check if parameter is sensitive
            is_sensitive = any(sensitive in key_lower for sensitive in SENSITIVE_KEYS)

            if is_sensitive:
                params.append(f"{key}=[Filtered]")
            else:
                params.append(param)
        else:
            params.append(param)

    return "&".join(params)


def init_sentry(settings: Settings) -> None:
    """Initialize Sentry error tracking.

    Args:
        settings: Application settings
    """
    if not settings.sentry_dsn:
        logger.info("Sentry DSN not configured, error tracking disabled")
        return

    # Determine environment
    environment = "development"
    if settings.sentry_environment:
        environment = settings.sentry_environment

    # Configure logging integration
    logging_integration = LoggingIntegration(
        level=logging.INFO,  # Capture info and above as breadcrumbs
        event_level=logging.ERROR,  # Send errors as events
    )

    # Initialize Sentry
    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        environment=environment,
        release=settings.sentry_release or "unknown",
        traces_sample_rate=settings.sentry_traces_sample_rate,
        profiles_sample_rate=settings.sentry_profiles_sample_rate,
        before_send=before_send,
        integrations=[
            FastApiIntegration(transaction_style="url"),
            RedisIntegration(),
            logging_integration,
        ],
        # Performance
        enable_tracing=True,
        # Privacy
        send_default_pii=False,  # Don't send PII by default
        attach_stacktrace=True,  # Include stack traces
        # Additional options
        debug=False,  # Set to True for debugging Sentry itself
    )

    logger.info(
        f"Sentry initialized for environment '{environment}' with release '{settings.sentry_release or 'unknown'}'"
    )


def capture_exception(error: Exception, **context: Any) -> None:
    """Capture an exception with additional context.

    Args:
        error: Exception to capture
        **context: Additional context to include
    """
    if context:
        with sentry_sdk.isolation_scope() as scope:
            # Add context
            for key, value in context.items():
                scope.set_context(key, value)

            # Capture exception
            sentry_sdk.capture_exception(error)
    else:
        # No context - direct capture
        sentry_sdk.capture_exception(error)


def capture_message(
    message: str,
    level: Literal["fatal", "critical", "error", "warning", "info", "debug"] = "info",
    **context: Any,
) -> None:
    """Capture a message with additional context.

    Args:
        message: Message to capture
        level: Severity level (debug, info, warning, error, fatal)
        **context: Additional context to include
    """
    if context:
        with sentry_sdk.isolation_scope() as scope:
            # Add context
            for key, value in context.items():
                scope.set_context(key, value)

            # Capture message
            sentry_sdk.capture_message(message, level=level)
    else:
        # No context - direct capture
        sentry_sdk.capture_message(message, level=level)


def set_user(user_id: str, **user_data: Any) -> None:
    """Set user context for error tracking.

    Args:
        user_id: User identifier (phone number, etc.)
        **user_data: Additional user data
    """
    sentry_sdk.set_user({"id": user_id, **user_data})


def set_tag(key: str, value: str) -> None:
    """Set a tag for error grouping.

    Args:
        key: Tag key
        value: Tag value
    """
    sentry_sdk.set_tag(key, value)


def set_context(key: str, value: dict[str, Any]) -> None:
    """Set additional context for errors.

    Args:
        key: Context key
        value: Context data
    """
    sentry_sdk.set_context(key, value)
