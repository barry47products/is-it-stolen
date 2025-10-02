"""Pytest configuration and shared fixtures."""
import pytest
from fastapi.testclient import TestClient

from src.presentation.api.app import app


@pytest.fixture
def client() -> TestClient:
    """Create FastAPI test client.

    Returns:
        TestClient instance for testing FastAPI endpoints
    """
    return TestClient(app)
