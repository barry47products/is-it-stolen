"""Tests for application settings."""

import os

from src.infrastructure.config.settings import Settings, get_settings


class TestSettings:
    """Test application settings."""

    def test_creates_settings_with_defaults(self) -> None:
        """Should create settings with default values."""
        # Arrange & Act
        settings = Settings()

        # Assert - Values loaded from environment or .env.test file
        assert settings.database_url.startswith("postgresql://")
        assert "isitstolen" in settings.database_url
        assert settings.redis_url.startswith("redis://")
        assert settings.environment == "test"
        assert settings.debug is True

    def test_loads_settings_from_environment_variables(self) -> None:
        """Should load settings from environment variables."""
        # Arrange
        os.environ["DATABASE_URL"] = "postgresql://test:test@localhost:5555/test"
        os.environ["REDIS_URL"] = "redis://localhost:6380"
        os.environ["ENVIRONMENT"] = "testing"
        os.environ["DEBUG"] = "true"

        # Act
        settings = Settings()

        # Assert
        assert settings.database_url == "postgresql://test:test@localhost:5555/test"
        assert settings.redis_url == "redis://localhost:6380"
        assert settings.environment == "testing"
        assert settings.debug is True

        # Cleanup
        del os.environ["DATABASE_URL"]
        del os.environ["REDIS_URL"]
        del os.environ["ENVIRONMENT"]
        del os.environ["DEBUG"]

    def test_get_settings_returns_cached_instance(self) -> None:
        """Should return same cached instance on multiple calls."""
        # Arrange & Act
        settings1 = get_settings()
        settings2 = get_settings()

        # Assert
        assert settings1 is settings2

    def test_settings_are_case_insensitive(self) -> None:
        """Should handle case-insensitive environment variables."""
        # Arrange
        os.environ["DATABASE_URL"] = "postgresql://test:test@localhost:5555/test"

        # Act
        settings = Settings()

        # Assert
        assert settings.database_url == "postgresql://test:test@localhost:5555/test"

        # Cleanup
        del os.environ["DATABASE_URL"]

    def test_whatsapp_settings_can_be_loaded(self) -> None:
        """Should load WhatsApp settings from environment."""
        # Arrange & Act
        settings = Settings()

        # Assert - Settings loaded from .env file (placeholders or actual values)
        assert settings.whatsapp_phone_number_id is not None
        assert settings.whatsapp_access_token is not None
        assert settings.whatsapp_business_account_id is not None
        assert settings.whatsapp_webhook_verify_token is not None
        assert settings.whatsapp_app_secret is not None
