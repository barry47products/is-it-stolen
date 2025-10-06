"""Structured logging configuration using structlog."""

import logging
import sys
from typing import Any

import structlog

from src.infrastructure.logging.context import add_request_id_processor
from src.infrastructure.logging.processors import (
    add_hashed_phone,
    filter_sensitive_data,
)


def configure_logging(
    log_level: str = "info",
    log_format: str = "console",
    redact_sensitive: bool = True,
) -> None:
    """Configure structured logging for the application.

    Sets up structlog with appropriate processors based on environment
    and configuration.

    Args:
        log_level: Logging level (debug, info, warning, error, critical)
        log_format: Output format - "json" for production, "console" for development
        redact_sensitive: Whether to redact sensitive data from logs
    """
    # Convert log level string to logging constant
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)

    # Build processor chain
    processors: list[Any] = [
        # Add log level
        structlog.stdlib.add_log_level,
        # Add logger name
        structlog.stdlib.add_logger_name,
        # Add timestamp
        structlog.processors.TimeStamper(fmt="iso"),
        # Add request ID from context
        add_request_id_processor,
    ]

    # Add privacy processors if enabled
    if redact_sensitive:
        processors.append(add_hashed_phone)
        processors.append(filter_sensitive_data)

    # Add stack info for exceptions
    processors.append(structlog.processors.StackInfoRenderer())
    processors.append(structlog.processors.format_exc_info)

    # Choose renderer based on format
    if log_format == "json":
        # JSON output for production (machine-readable)
        processors.append(structlog.processors.JSONRenderer())
    else:
        # Coloured console output for development (human-readable)
        processors.extend(
            [
                structlog.dev.ConsoleRenderer(
                    colors=True,
                    exception_formatter=structlog.dev.plain_traceback,
                )
            ]
        )

    # Configure structlog
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Configure standard logging to work with structlog
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=numeric_level,
        force=True,  # Override any existing configuration
    )

    # Set log level for root logger
    logging.root.setLevel(numeric_level)

    # Reduce noise from third-party libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
