"""Unit tests for metrics endpoint."""

from unittest.mock import MagicMock, patch

import pytest
from fastapi import status
from fastapi.testclient import TestClient


class TestMetricsEndpoint:
    """Test metrics endpoint."""

    @pytest.fixture
    def client(self) -> TestClient:
        """Create test client for metrics endpoint."""
        from fastapi import FastAPI

        from src.presentation.api.v1.metrics import router

        app = FastAPI()
        app.include_router(router)
        return TestClient(app)

    @patch("src.presentation.api.v1.metrics.get_metrics_service")
    def test_get_metrics_returns_all_metrics(
        self, mock_get_service: MagicMock, client: TestClient
    ) -> None:
        """Test GET /metrics returns all metrics."""
        # Arrange
        mock_service = MagicMock()
        mock_service.get_all_metrics.return_value = {
            "messages_received": 100,
            "messages_sent": 95,
            "reports_created": 25,
            "items_checked": 70,
            "average_response_time": 0.234,
            "active_users": 15,
            "timestamp": "2025-10-05T10:00:00",
        }
        mock_get_service.return_value = mock_service

        # Act
        response = client.get("/metrics")

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["messages_received"] == 100
        assert data["messages_sent"] == 95
        assert data["reports_created"] == 25
        assert data["items_checked"] == 70
        assert data["average_response_time"] == 0.234
        assert data["active_users"] == 15
        assert "timestamp" in data

    @patch("src.presentation.api.v1.metrics.get_metrics_service")
    def test_post_metrics_reset_resets_all_metrics(
        self, mock_get_service: MagicMock, client: TestClient
    ) -> None:
        """Test POST /metrics/reset resets all metrics."""
        # Arrange
        mock_service = MagicMock()
        mock_get_service.return_value = mock_service

        # Act
        response = client.post("/metrics/reset")

        # Assert
        assert response.status_code == status.HTTP_200_OK
        mock_service.reset_metrics.assert_called_once()
        data = response.json()
        assert data["message"] == "Metrics reset successfully"

    @patch("src.presentation.api.v1.metrics.get_metrics_service")
    def test_get_metrics_includes_all_required_fields(
        self, mock_get_service: MagicMock, client: TestClient
    ) -> None:
        """Test metrics response includes all required fields."""
        # Arrange
        mock_service = MagicMock()
        mock_service.get_all_metrics.return_value = {
            "messages_received": 10,
            "messages_sent": 10,
            "reports_created": 5,
            "items_checked": 3,
            "average_response_time": 0.1,
            "active_users": 2,
            "timestamp": "2025-10-05T10:00:00",
        }
        mock_get_service.return_value = mock_service

        # Act
        response = client.get("/metrics")

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "messages_received" in data
        assert "messages_sent" in data
        assert "reports_created" in data
        assert "items_checked" in data
        assert "average_response_time" in data
        assert "active_users" in data
        assert "timestamp" in data
