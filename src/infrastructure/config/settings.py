"""Application settings configuration."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=(".env.test", ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Database
    # SECURITY: Never commit real database passwords to the repository
    # Set DATABASE_URL environment variable in production
    database_url: str

    # Redis
    redis_url: str = "redis://localhost:6379"

    # WhatsApp
    whatsapp_phone_number_id: str = ""
    whatsapp_access_token: str = ""
    whatsapp_business_account_id: str = ""
    whatsapp_webhook_verify_token: str = ""
    whatsapp_app_secret: str = ""

    # Application
    environment: str = "development"
    debug: bool = False


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance.

    Returns:
        Settings instance
    """
    return Settings()
