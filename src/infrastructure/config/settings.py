"""Application settings configuration."""

from functools import lru_cache
from pathlib import Path

from pydantic import (
    Field,
    PostgresDsn,
    RedisDsn,
    field_validator,
    model_validator,
)
from pydantic_settings import BaseSettings, SettingsConfigDict

MIN_PORT = 1
MAX_PORT = 65535
MIN_TIMEOUT = 1
MAX_SESSION_TTL = 604800  # 7 days in seconds
MIN_RATE_LIMIT = 1


class Settings(BaseSettings):
    """Application settings loaded from environment variables.

    All settings are loaded from environment variables or .env files.
    Validation ensures type safety and fail-fast on invalid configuration.
    """

    model_config = SettingsConfigDict(
        env_file=(".env.test", ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Server Configuration
    port: int = Field(
        default=8000,
        ge=MIN_PORT,
        le=MAX_PORT,
        description="Server port number (1-65535)",
    )
    # Binding to 0.0.0.0 is required for Docker/container deployments
    host: str = Field(
        default="0.0.0.0",  # nosec B104
        description="Server host address",
    )

    # Database
    # SECURITY: Never commit real database passwords to the repository
    # Set DATABASE_URL environment variable in production
    database_url: PostgresDsn = Field(
        ..., description="PostgreSQL database connection URL"
    )

    # Redis
    redis_url: RedisDsn = Field(
        default=RedisDsn("redis://localhost:6379"),
        description="Redis connection URL",
    )

    # WhatsApp Business Cloud API
    whatsapp_phone_number_id: str = Field(
        default="", description="WhatsApp phone number ID"
    )
    whatsapp_access_token: str = Field(default="", description="WhatsApp access token")
    whatsapp_business_account_id: str = Field(
        default="", description="WhatsApp business account ID"
    )
    whatsapp_webhook_verify_token: str = Field(
        default="", description="WhatsApp webhook verification token"
    )
    whatsapp_app_secret: str = Field(default="", description="WhatsApp app secret")

    # Session Configuration
    session_ttl: int = Field(
        default=86400,
        ge=MIN_TIMEOUT,
        le=MAX_SESSION_TTL,
        description="Session TTL in seconds (1-604800)",
    )
    conversation_timeout: int = Field(
        default=600,
        ge=MIN_TIMEOUT,
        description="Conversation timeout in seconds",
    )

    # Rate Limiting (User-based)
    rate_limit_window_seconds: int = Field(
        default=60,
        ge=MIN_RATE_LIMIT,
        description="Rate limit window in seconds (per user/phone number)",
    )
    rate_limit_max_requests: int = Field(
        default=10,
        ge=MIN_RATE_LIMIT,
        description="Max requests per rate limit window (per user/phone number)",
    )

    # Rate Limiting (IP-based for webhooks)
    ip_rate_limit_window_seconds: int = Field(
        default=60,
        ge=MIN_RATE_LIMIT,
        description="IP rate limit window in seconds (for webhook endpoints)",
    )
    ip_rate_limit_max_requests: int = Field(
        default=100,
        ge=MIN_RATE_LIMIT,
        description="Max webhook requests per IP in time window",
    )

    # Rate Limiting Bypass (Admin/Testing)
    rate_limit_bypass_enabled: bool = Field(
        default=False,
        description="Enable rate limit bypass for admin/testing (ONLY use in dev/test)",
    )
    rate_limit_bypass_keys: str = Field(
        default="",
        description="Comma-separated list of keys to bypass (phone numbers or IPs)",
    )

    # Media Storage
    media_storage_path: Path = Field(
        default=Path("./uploads"),
        description="Path to media storage directory",
    )
    media_max_size_mb: int = Field(
        default=10, ge=1, le=100, description="Max media file size in MB"
    )

    # Logging
    log_level: str = Field(
        default="info",
        description="Logging level (debug, info, warning, error)",
    )
    log_format: str = Field(
        default="console",
        description="Log output format (console for development, json for production)",
    )
    log_redact_sensitive: bool = Field(
        default=True,
        description="Whether to redact sensitive data from logs (passwords, tokens, etc.)",
    )

    # Sentry Error Tracking
    sentry_dsn: str = Field(
        default="",
        description="Sentry DSN for error tracking (leave empty to disable)",
    )
    sentry_environment: str = Field(
        default="development",
        description="Sentry environment (development, staging, production)",
    )
    sentry_release: str = Field(
        default="",
        description="Sentry release version (e.g., git SHA or version number)",
    )
    sentry_traces_sample_rate: float = Field(
        default=0.1,
        ge=0.0,
        le=1.0,
        description="Sentry traces sample rate (0.0-1.0, 0.1 = 10%)",
    )
    sentry_profiles_sample_rate: float = Field(
        default=0.1,
        ge=0.0,
        le=1.0,
        description="Sentry profiles sample rate (0.0-1.0, 0.1 = 10%)",
    )

    # Application
    environment: str = Field(
        default="development",
        description="Application environment (development, test, production)",
    )
    debug: bool = Field(default=False, description="Enable debug mode")

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, value: str) -> str:
        """Validate log level is one of the allowed values."""
        allowed_levels = {"debug", "info", "warning", "error", "critical"}
        if value.lower() not in allowed_levels:
            raise ValueError(f"log_level must be one of {allowed_levels}, got: {value}")
        return value.lower()

    @field_validator("log_format")
    @classmethod
    def validate_log_format(cls, value: str) -> str:
        """Validate log format is one of the allowed values."""
        allowed_formats = {"console", "json"}
        if value.lower() not in allowed_formats:
            raise ValueError(
                f"log_format must be one of {allowed_formats}, got: {value}"
            )
        return value.lower()

    @field_validator("environment")
    @classmethod
    def validate_environment(cls, value: str) -> str:
        """Validate environment is one of the allowed values."""
        allowed_envs = {"development", "test", "staging", "production"}
        if value.lower() not in allowed_envs:
            raise ValueError(f"environment must be one of {allowed_envs}, got: {value}")
        return value.lower()

    @model_validator(mode="after")
    def validate_production_settings(self) -> "Settings":
        """Validate required settings for production environment."""
        if self.environment == "production":
            required_fields = [
                ("whatsapp_phone_number_id", "WhatsApp Phone Number ID"),
                ("whatsapp_access_token", "WhatsApp Access Token"),
                (
                    "whatsapp_business_account_id",
                    "WhatsApp Business Account ID",
                ),
                (
                    "whatsapp_webhook_verify_token",
                    "WhatsApp Webhook Verify Token",
                ),
                ("whatsapp_app_secret", "WhatsApp App Secret"),
            ]

            for field_name, display_name in required_fields:
                field_value = getattr(self, field_name)
                if not field_value or field_value.strip() == "":
                    raise ValueError(
                        f"{display_name} is required in production environment"
                    )

        return self


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance.

    Returns:
        Settings instance
    """
    return Settings()
