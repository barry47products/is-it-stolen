"""Unit tests for application startup logging."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from src.infrastructure.config.settings import Settings


class TestAppStartupLogging:
    """Test application startup logging behaviour."""

    @pytest.mark.asyncio
    @patch("src.presentation.api.app.init_sentry")
    @patch("src.presentation.api.app.init_db")
    @patch("src.presentation.api.app.get_settings")
    async def test_logs_sentry_initialization_when_dsn_configured(
        self,
        mock_get_settings: MagicMock,
        mock_init_db: MagicMock,
        mock_init_sentry: MagicMock,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Test that Sentry initialization is logged when DSN is configured."""
        # Arrange
        from src.presentation.api.app import lifespan

        settings = Settings(
            database_url="postgresql://user:pass@localhost/test",
            sentry_dsn="https://key@sentry.io/project",
            sentry_environment="test",
        )
        mock_get_settings.return_value = settings

        # Create a mock app
        mock_app = MagicMock()

        # Act
        async with lifespan(mock_app):
            pass

        # Assert - verify Sentry initialization was logged
        assert "Sentry initialized" in caplog.text
        assert "test" in caplog.text  # sentry_environment value

    @pytest.mark.asyncio
    @patch("src.presentation.api.app.init_sentry")
    @patch("src.presentation.api.app.init_db")
    @patch("src.presentation.api.app.get_logger")
    @patch("src.presentation.api.app.get_settings")
    async def test_does_not_log_sentry_when_dsn_not_configured(
        self,
        mock_get_settings: MagicMock,
        mock_get_logger: MagicMock,
        mock_init_db: MagicMock,
        mock_init_sentry: MagicMock,
    ) -> None:
        """Test that Sentry initialization is NOT logged when DSN is empty."""
        # Arrange
        from src.presentation.api.app import lifespan

        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger

        settings = Settings(
            database_url="postgresql://user:pass@localhost/test",
            sentry_dsn="",  # Empty DSN - Sentry disabled
        )
        mock_get_settings.return_value = settings

        # Create a mock app
        mock_app = MagicMock()

        # Act
        async with lifespan(mock_app):
            pass

        # Assert - verify Sentry initialization was NOT logged
        sentry_log_calls = [
            call
            for call in mock_logger.info.call_args_list
            if len(call[0]) > 0 and "Sentry initialized" in call[0][0]
        ]

        assert len(sentry_log_calls) == 0
