"""Tests for logging configuration."""

from __future__ import annotations

import logging
from unittest.mock import MagicMock, patch

import structlog


class TestConfigureLogging:
    """Test logging configuration."""

    @patch("structlog.configure")
    @patch("logging.basicConfig")
    def test_configures_with_console_format(
        self,
        mock_basic_config: MagicMock,
        mock_structlog_configure: MagicMock,
    ) -> None:
        """Test that console format is configured correctly."""
        # Arrange
        from src.infrastructure.logging.logging_config import configure_logging

        # Act
        configure_logging(log_level="info", log_format="console", redact_sensitive=True)

        # Assert - verify structlog was configured
        mock_structlog_configure.assert_called_once()
        call_kwargs = mock_structlog_configure.call_args[1]

        # Verify processors were added
        processors = call_kwargs["processors"]
        assert len(processors) > 0

        # Verify ConsoleRenderer is in processors (not JSONRenderer)
        processor_types = [type(p).__name__ for p in processors]
        assert "ConsoleRenderer" in processor_types
        assert "JSONRenderer" not in processor_types

    @patch("structlog.configure")
    @patch("logging.basicConfig")
    def test_configures_with_json_format(
        self,
        mock_basic_config: MagicMock,
        mock_structlog_configure: MagicMock,
    ) -> None:
        """Test that JSON format is configured correctly."""
        # Arrange
        from src.infrastructure.logging.logging_config import configure_logging

        # Act
        configure_logging(log_level="info", log_format="json", redact_sensitive=True)

        # Assert - verify structlog was configured
        mock_structlog_configure.assert_called_once()
        call_kwargs = mock_structlog_configure.call_args[1]

        # Verify processors were added
        processors = call_kwargs["processors"]
        assert len(processors) > 0

        # Verify JSONRenderer is in processors (not ConsoleRenderer)
        processor_types = [type(p).__name__ for p in processors]
        assert "JSONRenderer" in processor_types
        assert "ConsoleRenderer" not in processor_types

    @patch("structlog.configure")
    @patch("logging.basicConfig")
    def test_adds_privacy_processors_when_redact_enabled(
        self,
        mock_basic_config: MagicMock,
        mock_structlog_configure: MagicMock,
    ) -> None:
        """Test that privacy processors are added when redact_sensitive is True."""
        # Arrange
        from src.infrastructure.logging.logging_config import configure_logging

        # Act
        configure_logging(log_level="info", log_format="console", redact_sensitive=True)

        # Assert
        mock_structlog_configure.assert_called_once()
        call_kwargs = mock_structlog_configure.call_args[1]
        processors = call_kwargs["processors"]

        # Check that privacy processors are present
        # (add_hashed_phone and filter_sensitive_data are functions, not classes)
        processor_names = [
            p.__name__ if hasattr(p, "__name__") else type(p).__name__
            for p in processors
        ]

        assert "add_hashed_phone" in processor_names
        assert "filter_sensitive_data" in processor_names

    @patch("structlog.configure")
    @patch("logging.basicConfig")
    def test_skips_privacy_processors_when_redact_disabled(
        self,
        mock_basic_config: MagicMock,
        mock_structlog_configure: MagicMock,
    ) -> None:
        """Test that privacy processors are NOT added when redact_sensitive is False."""
        # Arrange
        from src.infrastructure.logging.logging_config import configure_logging

        # Act
        configure_logging(
            log_level="info", log_format="console", redact_sensitive=False
        )

        # Assert
        mock_structlog_configure.assert_called_once()
        call_kwargs = mock_structlog_configure.call_args[1]
        processors = call_kwargs["processors"]

        # Check that privacy processors are NOT present
        processor_names = [
            p.__name__ if hasattr(p, "__name__") else type(p).__name__
            for p in processors
        ]

        assert "add_hashed_phone" not in processor_names
        assert "filter_sensitive_data" not in processor_names

    @patch("structlog.configure")
    @patch("logging.basicConfig")
    def test_sets_correct_log_level(
        self,
        mock_basic_config: MagicMock,
        mock_structlog_configure: MagicMock,
    ) -> None:
        """Test that log level is set correctly."""
        # Arrange
        from src.infrastructure.logging.logging_config import configure_logging

        # Act
        configure_logging(
            log_level="debug", log_format="console", redact_sensitive=True
        )

        # Assert - verify basicConfig was called with DEBUG level
        mock_basic_config.assert_called_once()
        call_kwargs = mock_basic_config.call_args[1]
        assert call_kwargs["level"] == logging.DEBUG

    @patch("structlog.configure")
    @patch("logging.basicConfig")
    def test_configures_structlog_wrapper_class(
        self,
        mock_basic_config: MagicMock,
        mock_structlog_configure: MagicMock,
    ) -> None:
        """Test that structlog is configured with BoundLogger wrapper."""
        # Arrange
        from src.infrastructure.logging.logging_config import configure_logging

        # Act
        configure_logging(log_level="info", log_format="console", redact_sensitive=True)

        # Assert
        mock_structlog_configure.assert_called_once()
        call_kwargs = mock_structlog_configure.call_args[1]
        assert call_kwargs["wrapper_class"] == structlog.stdlib.BoundLogger
        assert call_kwargs["cache_logger_on_first_use"] is True

    @patch("structlog.configure")
    @patch("logging.basicConfig")
    @patch("logging.getLogger")
    def test_reduces_third_party_logging_noise(
        self,
        mock_get_logger: MagicMock,
        mock_basic_config: MagicMock,
        mock_structlog_configure: MagicMock,
    ) -> None:
        """Test that third-party library logging is set to WARNING level."""
        # Arrange
        from src.infrastructure.logging.logging_config import configure_logging

        mock_httpx_logger = MagicMock()
        mock_httpcore_logger = MagicMock()
        mock_uvicorn_logger = MagicMock()

        logger_map = {
            "httpx": mock_httpx_logger,
            "httpcore": mock_httpcore_logger,
            "uvicorn.access": mock_uvicorn_logger,
        }

        def get_logger_side_effect(name: str) -> MagicMock:
            return logger_map.get(name, MagicMock())

        mock_get_logger.side_effect = get_logger_side_effect

        # Act
        configure_logging(log_level="info", log_format="console", redact_sensitive=True)

        # Assert
        mock_httpx_logger.setLevel.assert_called_once_with(logging.WARNING)
        mock_httpcore_logger.setLevel.assert_called_once_with(logging.WARNING)
        mock_uvicorn_logger.setLevel.assert_called_once_with(logging.WARNING)
