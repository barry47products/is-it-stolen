"""Tests for FastAPI application lifecycle management."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.presentation.api.app import create_app, lifespan


@pytest.mark.unit
class TestApplicationLifecycle:
    """Test application lifecycle management."""

    @pytest.mark.asyncio
    async def test_lifespan_startup_and_shutdown(self) -> None:
        """Test that lifespan handles startup and shutdown."""
        # Arrange
        app = FastAPI()

        # Act & Assert - lifespan should run without errors
        async with lifespan(app):
            # Startup completed, keywords should be loaded
            pass

            # Startup completed, lifespan runs without errors

        # After context exit, shutdown completed

    def test_create_app_returns_configured_app(self) -> None:
        """Test that create_app returns a properly configured FastAPI app."""
        # Act
        app = create_app()

        # Assert
        assert app.title == "Is It Stolen API"
        assert app.version == "0.1.0"
        assert "WhatsApp bot for checking and reporting stolen items" in app.description
        assert "Features" in app.description
        assert "Authentication" in app.description

    def test_create_app_includes_v1_routes(self) -> None:
        """Test that created app includes v1 API routes."""
        # Act
        app = create_app()
        client = TestClient(app)

        # Assert - v1 health endpoint should exist
        response = client.get("/v1/health")
        assert response.status_code == 200

    def test_create_app_includes_middleware(self) -> None:
        """Test that created app includes custom middleware."""
        # Act
        app = create_app()
        client = TestClient(app)

        # Assert - middleware should add request ID
        response = client.get("/health")
        assert "X-Request-ID" in response.headers

    def test_create_app_environment_based_docs(self) -> None:
        """Test that app configuration respects environment."""
        # Act
        app = create_app()

        # Assert - docs should be available in non-production
        # (Since we're in test environment, docs should be enabled)
        assert app.docs_url is not None
        assert app.redoc_url is not None
