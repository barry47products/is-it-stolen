"""Pytest configuration and shared fixtures."""

import os

import pytest
from fastapi.testclient import TestClient

from src.presentation.api.app import app


@pytest.fixture(scope="session", autouse=True)
def set_test_environment() -> None:
    """Set test environment variables before any tests run."""
    os.environ["ENVIRONMENT"] = "test"


@pytest.fixture
def client() -> TestClient:
    """Create FastAPI test client.

    Returns:
        TestClient instance for testing FastAPI endpoints
    """
    return TestClient(app)
