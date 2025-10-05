"""Pytest configuration and shared fixtures."""

import os

import pytest
from fastapi.testclient import TestClient

# Set test environment variables BEFORE importing any app modules
os.environ["ENVIRONMENT"] = "test"
# WhatsApp test credentials
os.environ["WHATSAPP_PHONE_NUMBER_ID"] = "test_phone_id"
os.environ["WHATSAPP_ACCESS_TOKEN"] = "test_access_token"
os.environ["WHATSAPP_BUSINESS_ACCOUNT_ID"] = "test_account_id"
os.environ["WHATSAPP_WEBHOOK_VERIFY_TOKEN"] = "test_verify_token"
os.environ["WHATSAPP_APP_SECRET"] = "test_app_secret"

from src.infrastructure.persistence.database import init_db
from src.presentation.api.app import app


@pytest.fixture(scope="session", autouse=True)
def set_test_environment() -> None:
    """Ensure test environment variables are set."""
    # Already set at module level to ensure they're available before imports
    pass


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
