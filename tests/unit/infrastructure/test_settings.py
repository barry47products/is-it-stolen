"""Tests for application settings."""

import os
from pathlib import Path

import pytest
from pydantic import ValidationError

from src.infrastructure.config.settings import Settings, get_settings


class TestSettings:
    """Test application settings."""

    def test_creates_settings_with_defaults(self) -> None:
        """Should create settings with default values."""
        # Arrange & Act
        settings = Settings()

        # Assert - Values loaded from environment or .env.test file
        assert str(settings.database_url).startswith("postgresql://")
        assert "isitstolen" in str(settings.database_url)
        assert str(settings.redis_url).startswith("redis://")
        assert settings.environment == "test"
        assert settings.debug is True

    def test_loads_settings_from_environment_variables(self) -> None:
        """Should load settings from environment variables."""
        # Arrange
        os.environ["DATABASE_URL"] = "postgresql://test:test@localhost:5555/test"
        os.environ["REDIS_URL"] = "redis://localhost:6380"
        os.environ["ENVIRONMENT"] = "development"
        os.environ["DEBUG"] = "true"

        # Act
        settings = Settings()

        # Assert
        assert (
            str(settings.database_url) == "postgresql://test:test@localhost:5555/test"
        )
        assert str(settings.redis_url).startswith("redis://localhost:6380")
        assert settings.environment == "development"
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
        assert (
            str(settings.database_url) == "postgresql://test:test@localhost:5555/test"
        )

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

    def test_rejects_invalid_database_url(self) -> None:
        """Should reject invalid database URL format."""
        # Arrange
        os.environ["DATABASE_URL"] = "not-a-valid-url"

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            Settings()

        assert "database_url" in str(exc_info.value).lower()

        # Cleanup
        del os.environ["DATABASE_URL"]

    def test_rejects_invalid_redis_url(self) -> None:
        """Should reject invalid Redis URL format."""
        # Arrange
        os.environ["DATABASE_URL"] = "postgresql://test:test@localhost:5555/test"
        os.environ["REDIS_URL"] = "not-a-valid-redis-url"

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            Settings()

        assert "redis_url" in str(exc_info.value).lower()

        # Cleanup
        del os.environ["DATABASE_URL"]
        del os.environ["REDIS_URL"]

    def test_rejects_invalid_port_number(self) -> None:
        """Should reject port numbers outside valid range."""
        # Arrange
        os.environ["DATABASE_URL"] = "postgresql://test:test@localhost:5555/test"
        os.environ["PORT"] = "99999"

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            Settings()

        assert "port" in str(exc_info.value).lower()

        # Cleanup
        del os.environ["DATABASE_URL"]
        del os.environ["PORT"]

    def test_rejects_negative_port_number(self) -> None:
        """Should reject negative port numbers."""
        # Arrange
        os.environ["DATABASE_URL"] = "postgresql://test:test@localhost:5555/test"
        os.environ["PORT"] = "-1"

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            Settings()

        assert "port" in str(exc_info.value).lower()

        # Cleanup
        del os.environ["DATABASE_URL"]
        del os.environ["PORT"]

    def test_rejects_invalid_log_level(self) -> None:
        """Should reject invalid log level values."""
        # Arrange
        os.environ["DATABASE_URL"] = "postgresql://test:test@localhost:5555/test"
        os.environ["LOG_LEVEL"] = "invalid"

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            Settings()

        error_msg = str(exc_info.value).lower()
        assert "log_level" in error_msg
        assert "invalid" in error_msg

        # Cleanup
        del os.environ["DATABASE_URL"]
        del os.environ["LOG_LEVEL"]

    def test_accepts_valid_log_levels(self) -> None:
        """Should accept all valid log level values."""
        # Arrange
        valid_levels = ["debug", "info", "warning", "error", "critical"]
        os.environ["DATABASE_URL"] = "postgresql://test:test@localhost:5555/test"

        # Act & Assert
        for level in valid_levels:
            os.environ["LOG_LEVEL"] = level
            settings = Settings()
            assert settings.log_level == level.lower()

        # Cleanup
        del os.environ["DATABASE_URL"]
        del os.environ["LOG_LEVEL"]

    def test_rejects_invalid_environment(self) -> None:
        """Should reject invalid environment values."""
        # Arrange
        os.environ["DATABASE_URL"] = "postgresql://test:test@localhost:5555/test"
        os.environ["ENVIRONMENT"] = "invalid"

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            Settings()

        error_msg = str(exc_info.value).lower()
        assert "environment" in error_msg
        assert "invalid" in error_msg

        # Cleanup
        del os.environ["DATABASE_URL"]
        del os.environ["ENVIRONMENT"]

    def test_accepts_valid_environments(self) -> None:
        """Should accept all valid environment values."""
        # Arrange
        valid_envs = ["development", "test", "staging", "production"]
        os.environ["DATABASE_URL"] = "postgresql://test:test@localhost:5555/test"

        # Act & Assert
        for env in valid_envs:
            os.environ["ENVIRONMENT"] = env
            # Skip production as it requires WhatsApp credentials
            if env != "production":
                settings = Settings()
                assert settings.environment == env.lower()

        # Cleanup
        del os.environ["DATABASE_URL"]
        del os.environ["ENVIRONMENT"]

    def test_production_requires_whatsapp_credentials(self) -> None:
        """Should require WhatsApp credentials in production environment."""
        # Arrange
        os.environ["DATABASE_URL"] = "postgresql://test:test@localhost:5555/test"
        os.environ["ENVIRONMENT"] = "production"
        os.environ["WHATSAPP_PHONE_NUMBER_ID"] = ""
        os.environ["WHATSAPP_ACCESS_TOKEN"] = ""

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            Settings()

        error_msg = str(exc_info.value).lower()
        assert "whatsapp" in error_msg or "production" in error_msg

        # Cleanup
        del os.environ["DATABASE_URL"]
        del os.environ["ENVIRONMENT"]
        del os.environ["WHATSAPP_PHONE_NUMBER_ID"]
        del os.environ["WHATSAPP_ACCESS_TOKEN"]

    def test_production_accepts_valid_whatsapp_credentials(self) -> None:
        """Should accept production config with valid WhatsApp credentials."""
        # Arrange
        os.environ["DATABASE_URL"] = "postgresql://test:test@localhost:5555/test"
        os.environ["ENVIRONMENT"] = "production"
        os.environ["WHATSAPP_PHONE_NUMBER_ID"] = "123456"
        os.environ["WHATSAPP_ACCESS_TOKEN"] = "token123"
        os.environ["WHATSAPP_BUSINESS_ACCOUNT_ID"] = "account123"
        os.environ["WHATSAPP_WEBHOOK_VERIFY_TOKEN"] = "verify123"
        os.environ["WHATSAPP_APP_SECRET"] = "secret123"

        # Act
        settings = Settings()

        # Assert
        assert settings.environment == "production"
        assert settings.whatsapp_phone_number_id == "123456"

        # Cleanup
        del os.environ["DATABASE_URL"]
        del os.environ["ENVIRONMENT"]
        del os.environ["WHATSAPP_PHONE_NUMBER_ID"]
        del os.environ["WHATSAPP_ACCESS_TOKEN"]
        del os.environ["WHATSAPP_BUSINESS_ACCOUNT_ID"]
        del os.environ["WHATSAPP_WEBHOOK_VERIFY_TOKEN"]
        del os.environ["WHATSAPP_APP_SECRET"]

    def test_rejects_session_ttl_exceeding_max(self) -> None:
        """Should reject session TTL exceeding maximum allowed."""
        # Arrange
        os.environ["DATABASE_URL"] = "postgresql://test:test@localhost:5555/test"
        os.environ["SESSION_TTL"] = "999999"

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            Settings()

        assert "session_ttl" in str(exc_info.value).lower()

        # Cleanup
        del os.environ["DATABASE_URL"]
        del os.environ["SESSION_TTL"]

    def test_loads_media_storage_settings(self) -> None:
        """Should load media storage configuration."""
        # Arrange
        os.environ["DATABASE_URL"] = "postgresql://test:test@localhost:5555/test"
        os.environ["MEDIA_STORAGE_PATH"] = "/tmp/test_media"
        os.environ["MEDIA_MAX_SIZE_MB"] = "50"

        # Act
        settings = Settings()

        # Assert
        assert settings.media_storage_path == Path("/tmp/test_media")
        assert settings.media_max_size_mb == 50

        # Cleanup
        del os.environ["DATABASE_URL"]
        del os.environ["MEDIA_STORAGE_PATH"]
        del os.environ["MEDIA_MAX_SIZE_MB"]

    def test_loads_rate_limiting_settings(self) -> None:
        """Should load rate limiting configuration."""
        # Arrange
        os.environ["DATABASE_URL"] = "postgresql://test:test@localhost:5555/test"
        os.environ["RATE_LIMIT_WINDOW_SECONDS"] = "30"
        os.environ["RATE_LIMIT_MAX_REQUESTS"] = "20"

        # Act
        settings = Settings()

        # Assert
        assert settings.rate_limit_window_seconds == 30
        assert settings.rate_limit_max_requests == 20

        # Cleanup
        del os.environ["DATABASE_URL"]
        del os.environ["RATE_LIMIT_WINDOW_SECONDS"]
        del os.environ["RATE_LIMIT_MAX_REQUESTS"]
