"""Tests for FastAPI application structure and middleware."""

import pytest
from fastapi.testclient import TestClient


@pytest.mark.unit
class TestAPIStructure:
    """Test API structure and configuration."""

    def test_versioned_health_endpoint_exists(self, client: TestClient) -> None:
        """Test that versioned health endpoint exists at /v1/health."""
        # Act
        response = client.get("/v1/health")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data

    def test_root_health_endpoint_exists(self, client: TestClient) -> None:
        """Test that root health endpoint exists at /health."""
        # Act
        response = client.get("/health")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data

    def test_docs_endpoint_available_in_non_production(
        self, client: TestClient
    ) -> None:
        """Test that documentation endpoints are available in non-production."""
        # Act
        docs_response = client.get("/docs")
        redoc_response = client.get("/redoc")

        # Assert - should redirect or be accessible
        assert docs_response.status_code in [200, 307]
        assert redoc_response.status_code in [200, 307]


@pytest.mark.unit
class TestMiddleware:
    """Test custom middleware functionality."""

    def test_request_id_header_added(self, client: TestClient) -> None:
        """Test that X-Request-ID header is added to responses."""
        # Act
        response = client.get("/health")

        # Assert
        assert "X-Request-ID" in response.headers
        # Should be a valid UUID format
        request_id = response.headers["X-Request-ID"]
        assert len(request_id) == 36  # UUID format
        assert request_id.count("-") == 4

    def test_logging_middleware_processes_requests(self, client: TestClient) -> None:
        """Test that logging middleware processes requests."""
        # Act
        response = client.get("/health")

        # Assert - response should be successful
        assert response.status_code == 200

    def test_multiple_requests_have_unique_ids(self, client: TestClient) -> None:
        """Test that each request gets a unique request ID."""
        # Act
        response1 = client.get("/health")
        response2 = client.get("/health")

        # Assert
        request_id1 = response1.headers["X-Request-ID"]
        request_id2 = response2.headers["X-Request-ID"]
        assert request_id1 != request_id2

    @pytest.mark.asyncio
    async def test_request_id_middleware_handles_non_http_connections(self) -> None:
        """Test that RequestIDMiddleware passes through non-HTTP connections."""
        from src.presentation.api.middleware import RequestIDMiddleware

        # Arrange
        called = False

        async def mock_app(scope, receive, send):  # type: ignore[no-untyped-def]
            nonlocal called
            called = True

        middleware = RequestIDMiddleware(app=mock_app)
        scope = {"type": "websocket"}  # Non-HTTP connection

        async def mock_receive():  # type: ignore[no-untyped-def]
            return {}

        async def mock_send(message):  # type: ignore[no-untyped-def]
            pass

        # Act
        await middleware(scope, mock_receive, mock_send)

        # Assert - should pass through to app without modification
        assert called

    @pytest.mark.asyncio
    async def test_logging_middleware_handles_non_http_connections(self) -> None:
        """Test that LoggingMiddleware passes through non-HTTP connections."""
        from src.presentation.api.middleware import LoggingMiddleware

        # Arrange
        called = False

        async def mock_app(scope, receive, send):  # type: ignore[no-untyped-def]
            nonlocal called
            called = True

        middleware = LoggingMiddleware(app=mock_app)
        scope = {"type": "lifespan"}  # Non-HTTP connection

        async def mock_receive():  # type: ignore[no-untyped-def]
            return {}

        async def mock_send(message):  # type: ignore[no-untyped-def]
            pass

        # Act
        await middleware(scope, mock_receive, mock_send)

        # Assert - should pass through to app without modification
        assert called


@pytest.mark.unit
class TestApplicationLifecycle:
    """Test application lifecycle management."""

    def test_application_starts_successfully(self, client: TestClient) -> None:
        """Test that application starts and responds to requests."""
        # Act
        response = client.get("/health")

        # Assert
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
