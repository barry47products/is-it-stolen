"""Unit tests for Prometheus metrics endpoint."""

import pytest
from fastapi import status
from fastapi.testclient import TestClient


class TestPrometheusEndpoint:
    """Test Prometheus metrics endpoint."""

    @pytest.fixture
    def client(self) -> TestClient:
        """Create test client for Prometheus endpoint."""
        from fastapi import FastAPI

        from src.presentation.api.prometheus import router

        app = FastAPI()
        app.include_router(router)
        return TestClient(app)

    def test_metrics_endpoint_returns_prometheus_format(
        self, client: TestClient
    ) -> None:
        """Test GET /metrics returns Prometheus format."""
        # Act
        response = client.get("/metrics")

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert "text/plain" in response.headers["content-type"]

        # Check for Prometheus format markers
        content = response.text
        assert "# HELP" in content or "# TYPE" in content

    def test_metrics_endpoint_includes_custom_metrics(self, client: TestClient) -> None:
        """Test that custom metrics are included in Prometheus output."""
        # Arrange - increment some metrics
        from src.infrastructure.metrics.metrics_service import get_metrics_service

        metrics = get_metrics_service()
        metrics.increment_messages_received()
        metrics.increment_messages_sent()

        # Act
        response = client.get("/metrics")

        # Assert
        content = response.text
        assert "messages_received_total" in content
        assert "messages_sent_total" in content

    def test_metrics_endpoint_includes_all_defined_metrics(
        self, client: TestClient
    ) -> None:
        """Test that all defined metrics appear in output."""
        # Act
        response = client.get("/metrics")

        # Assert
        content = response.text
        assert "messages_received_total" in content
        assert "messages_sent_total" in content
        assert "reports_created_total" in content
        assert "items_checked_total" in content
        assert "response_time_seconds" in content
        assert "active_users_total" in content
