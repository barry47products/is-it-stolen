"""Unit tests for health check endpoints."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import status
from fastapi.testclient import TestClient


class TestHealthEndpoints:
    """Test health check endpoints."""

    @pytest.fixture
    def client(self) -> TestClient:
        """Create test client for health endpoints."""
        from fastapi import FastAPI

        from src.presentation.api.v1.health import router

        app = FastAPI()
        app.include_router(router)
        return TestClient(app)

    def test_basic_health_check_returns_healthy_status(
        self, client: TestClient
    ) -> None:
        """Test GET /health returns healthy status."""
        # Act
        response = client.get("/health")

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
        assert isinstance(data["version"], str)

    @patch("src.presentation.api.v1.health.get_engine")
    def test_readiness_check_succeeds_when_all_dependencies_healthy(
        self, mock_get_engine: MagicMock, client: TestClient
    ) -> None:
        """Test GET /health/ready succeeds when DB and Redis are connected."""
        # Arrange
        mock_engine = MagicMock()
        mock_connection = MagicMock()
        mock_engine.connect.return_value.__enter__ = MagicMock(
            return_value=mock_connection
        )
        mock_engine.connect.return_value.__exit__ = MagicMock(return_value=None)
        mock_get_engine.return_value = mock_engine

        # Act
        with patch("src.presentation.api.v1.health.get_redis_client") as mock_redis:
            mock_redis_instance = AsyncMock()
            mock_redis_connection = AsyncMock()
            mock_redis_connection.ping = AsyncMock(return_value=True)
            mock_redis_instance._get_redis = AsyncMock(
                return_value=mock_redis_connection
            )
            mock_redis.return_value = mock_redis_instance

            response = client.get("/health/ready")

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "ready"
        assert data["database"] == "connected"
        assert data["redis"] == "connected"

    @patch("src.presentation.api.v1.health.get_engine")
    def test_readiness_check_fails_when_database_unavailable(
        self, mock_get_engine: MagicMock, client: TestClient
    ) -> None:
        """Test GET /health/ready fails when database is unavailable."""
        # Arrange
        mock_engine = MagicMock()
        mock_engine.connect.side_effect = Exception("Database connection failed")
        mock_get_engine.return_value = mock_engine

        # Act
        response = client.get("/health/ready")

        # Assert
        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
        data = response.json()
        assert data["status"] == "unavailable"
        assert data["database"] == "disconnected"

    @patch("src.presentation.api.v1.health.get_engine")
    def test_readiness_check_fails_when_redis_unavailable(
        self, mock_get_engine: MagicMock, client: TestClient
    ) -> None:
        """Test GET /health/ready fails when Redis is unavailable."""
        # Arrange
        mock_engine = MagicMock()
        mock_connection = MagicMock()
        mock_engine.connect.return_value.__enter__ = MagicMock(
            return_value=mock_connection
        )
        mock_engine.connect.return_value.__exit__ = MagicMock(return_value=None)
        mock_get_engine.return_value = mock_engine

        # Act
        with patch("src.presentation.api.v1.health.get_redis_client") as mock_redis:
            mock_redis_instance = AsyncMock()
            mock_redis_connection = AsyncMock()
            mock_redis_connection.ping = AsyncMock(side_effect=Exception("Redis error"))
            mock_redis_instance._get_redis = AsyncMock(
                return_value=mock_redis_connection
            )
            mock_redis.return_value = mock_redis_instance

            response = client.get("/health/ready")

        # Assert
        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
        data = response.json()
        assert data["status"] == "unavailable"
        assert data["redis"] == "disconnected"

    def test_liveness_check_returns_alive_status(self, client: TestClient) -> None:
        """Test GET /health/live returns alive status."""
        # Act
        response = client.get("/health/live")

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "alive"

    def test_health_endpoints_respond_quickly(self, client: TestClient) -> None:
        """Test health endpoints respond in under 100ms."""
        import time

        # Test basic health
        start = time.time()
        response = client.get("/health")
        duration_ms = (time.time() - start) * 1000
        assert response.status_code == status.HTTP_200_OK
        assert duration_ms < 100

        # Test liveness
        start = time.time()
        response = client.get("/health/live")
        duration_ms = (time.time() - start) * 1000
        assert response.status_code == status.HTTP_200_OK
        assert duration_ms < 100

    def test_health_check_includes_service_version(self, client: TestClient) -> None:
        """Test health check includes service version."""
        # Act
        response = client.get("/health")

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "version" in data
        assert data["version"] == "0.1.0"

    @patch("src.presentation.api.v1.health.get_engine")
    def test_readiness_check_includes_all_dependencies(
        self, mock_get_engine: MagicMock, client: TestClient
    ) -> None:
        """Test readiness check includes all critical dependencies."""
        # Arrange
        mock_engine = MagicMock()
        mock_connection = MagicMock()
        mock_engine.connect.return_value.__enter__ = MagicMock(
            return_value=mock_connection
        )
        mock_engine.connect.return_value.__exit__ = MagicMock(return_value=None)
        mock_get_engine.return_value = mock_engine

        # Act
        with patch("src.presentation.api.v1.health.get_redis_client") as mock_redis:
            mock_redis_instance = AsyncMock()
            mock_redis_connection = AsyncMock()
            mock_redis_connection.ping = AsyncMock(return_value=True)
            mock_redis_instance._get_redis = AsyncMock(
                return_value=mock_redis_connection
            )
            mock_redis.return_value = mock_redis_instance

            response = client.get("/health/ready")

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "database" in data
        assert "redis" in data
        assert data["database"] == "connected"
        assert data["redis"] == "connected"
