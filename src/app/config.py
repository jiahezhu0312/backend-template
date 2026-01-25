"""Application configuration using Pydantic Settings."""

from functools import lru_cache
from typing import Literal

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Application
    env: Literal["local", "test", "staging", "production"] = "local"
    debug: bool = False

    # Database
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/app"

    # Logging
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    log_format: Literal["console", "json"] = "console"

    # CORS - comma-separated list of allowed origins
    cors_origins: str = ""

    @property
    def is_production(self) -> bool:
        return self.env == "production"

    @property
    def is_test(self) -> bool:
        return self.env == "test"

    @property
    def cors_origins_list(self) -> list[str]:
        """Parse comma-separated CORS origins into a list."""
        if not self.cors_origins:
            return []
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @model_validator(mode="after")
    def validate_production_settings(self) -> "Settings":
        """Ensure production has secure configuration."""
        if self.env == "production":
            # Reject default database credentials in production
            if "postgres:postgres@" in self.database_url:
                raise ValueError(
                    "Default database credentials not allowed in production. "
                    "Set DATABASE_URL with secure credentials."
                )
        return self


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance.

    Use clear_settings_cache() in tests to reset between test runs.
    """
    return Settings()


def clear_settings_cache() -> None:
    """Clear the settings cache.

    Call this in test fixtures when you need to reload settings
    with different environment variables.
    """
    get_settings.cache_clear()
