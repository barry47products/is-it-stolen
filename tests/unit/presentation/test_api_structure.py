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
        assert response.json() == {"status": "healthy", "api_version": "v1"}

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
