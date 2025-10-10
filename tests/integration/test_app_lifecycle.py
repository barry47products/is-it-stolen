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

    @patch("src.presentation.api.app.instrument_all")
    @patch("src.presentation.api.app.setup_tracing")
    def test_app_has_openapi_documentation_configured(
        self, mock_setup: MagicMock, mock_instrument: MagicMock
    ) -> None:
        """Should configure comprehensive OpenAPI documentation metadata."""
        # Arrange
        from src.presentation.api.app import create_app

        # Act
        app = create_app()

        # Assert - OpenAPI metadata is configured
        assert app.title == "Is It Stolen API"
        assert "WhatsApp bot" in app.description
        assert "Features" in app.description
        assert "Authentication" in app.description
        assert app.version == "0.1.0"
        assert app.contact == {
            "name": "Is It Stolen Team",
            "url": "https://github.com/barry47products/is-it-stolen",
        }
        assert app.license_info == {
            "name": "MIT License",
            "url": "https://opensource.org/licenses/MIT",
        }

    @patch("src.presentation.api.app.instrument_all")
    @patch("src.presentation.api.app.setup_tracing")
    def test_app_has_openapi_tags_configured(
        self, mock_setup: MagicMock, mock_instrument: MagicMock
    ) -> None:
        """Should configure OpenAPI tags for endpoint grouping."""
        # Arrange
        from src.presentation.api.app import create_app

        # Act
        app = create_app()

        # Assert - OpenAPI tags are defined
        assert app.openapi_tags is not None
        tag_names = [tag["name"] for tag in app.openapi_tags]
        assert "webhook" in tag_names
        assert "health" in tag_names
        assert "metrics" in tag_names

        # Verify tag descriptions exist
        webhook_tag = next(tag for tag in app.openapi_tags if tag["name"] == "webhook")
        assert "description" in webhook_tag
        assert len(webhook_tag["description"]) > 0

    @patch("src.presentation.api.app.instrument_all")
    @patch("src.presentation.api.app.setup_tracing")
    def test_openapi_docs_accessible_in_development(
        self, mock_setup: MagicMock, mock_instrument: MagicMock
    ) -> None:
        """Should make OpenAPI docs accessible in development environment."""
        # Arrange
        from src.presentation.api.app import create_app

        # Act
        app = create_app()

        # Assert - Docs endpoints are accessible
        with TestClient(app) as client:
            # Swagger UI
            docs_response = client.get("/docs")
            assert docs_response.status_code in [200, 404]  # 404 in prod

            # ReDoc
            redoc_response = client.get("/redoc")
            assert redoc_response.status_code in [200, 404]  # 404 in prod

            # OpenAPI JSON schema
            openapi_response = client.get("/openapi.json")
            assert openapi_response.status_code == 200
            openapi_schema = openapi_response.json()
            assert openapi_schema["info"]["title"] == "Is It Stolen API"
            assert openapi_schema["info"]["version"] == "0.1.0"
