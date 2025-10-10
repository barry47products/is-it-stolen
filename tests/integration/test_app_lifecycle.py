"""Integration tests for application lifecycle management."""

from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient


class TestAppLifecycle:
    """Test application startup and shutdown lifecycle."""

    @patch("src.presentation.api.app.instrument_all")
    @patch("src.presentation.api.app.setup_tracing")
    def test_app_startup_with_tracing_enabled(
        self, mock_setup: MagicMock, mock_instrument: MagicMock
    ) -> None:
        """Should initialize tracing when enabled in settings."""
        # Arrange
        from src.presentation.api.app import create_app

        # Act
        app = create_app()
        with TestClient(app) as client:
            # Assert - app starts successfully
            response = client.get("/health")
            assert response.status_code == 200

        # Verify tracing was set up
        mock_setup.assert_called()
        mock_instrument.assert_called()

    @patch("src.presentation.api.app.instrument_all")
    @patch("src.presentation.api.app.setup_tracing")
    @patch("src.presentation.api.app.get_settings")
    def test_app_startup_with_tracing_disabled(
        self,
        mock_get_settings: MagicMock,
        mock_setup: MagicMock,
        mock_instrument: MagicMock,
    ) -> None:
        """Should skip instrumentation when tracing disabled in settings."""
        # Arrange
        from src.infrastructure.config.settings import Settings
        from src.presentation.api.app import create_app

        # Create a real settings object with tracing disabled
        mock_settings = Settings(
            database_url="postgresql://test:test@localhost/test",  # pragma: allowlist secret
            otel_enabled=False,
        )
        mock_get_settings.return_value = mock_settings

        # Act
        app = create_app()
        with TestClient(app) as client:
            # Assert - app starts successfully without instrumentation
            response = client.get("/health")
            assert response.status_code == 200

        # Verify setup_tracing was called but instrument_all was not
        mock_setup.assert_called()
        mock_instrument.assert_not_called()
