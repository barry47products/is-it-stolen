"""Pytest configuration and shared fixtures."""

import os

import pytest
from fastapi.testclient import TestClient

from src.infrastructure.persistence.database import init_db
from src.presentation.api.app import app


@pytest.fixture(scope="session", autouse=True)
def set_test_environment() -> None:
    """Set test environment variables before any tests run."""
    os.environ["ENVIRONMENT"] = "test"


@pytest.fixture(scope="session", autouse=True)
def initialize_database() -> None:
    """Initialize database tables before running integration tests.

    This fixture runs once per test session and ensures all tables
    are created before any integration tests run. It depends on
    set_test_environment to ensure ENVIRONMENT is set to 'test'.
    """
    init_db()


@pytest.fixture
def client() -> TestClient:
    """Create FastAPI test client.

    Returns:
        TestClient instance for testing FastAPI endpoints
    """
    return TestClient(app)
