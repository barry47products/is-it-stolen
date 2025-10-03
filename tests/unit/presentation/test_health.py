"""Tests for health check endpoint."""

import pytest
from fastapi.testclient import TestClient


@pytest.mark.unit
def test_health_check_returns_healthy_status(client: TestClient) -> None:
    """Test that health check endpoint returns healthy status.

    Given: A running FastAPI application
    When: GET request is made to /health endpoint
    Then: Response status is 200 and body contains healthy status
    """
    # Act
    response = client.get("/health")

    # Assert
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


@pytest.mark.unit
def test_health_check_has_correct_content_type(client: TestClient) -> None:
    """Test that health check endpoint returns JSON content type.

    Given: A running FastAPI application
    When: GET request is made to /health endpoint
    Then: Response content type is application/json
    """
    # Act
    response = client.get("/health")

    # Assert
    assert response.headers["content-type"] == "application/json"
