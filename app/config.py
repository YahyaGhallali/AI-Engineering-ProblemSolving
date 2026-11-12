"""Configuration module for Nova Support AI.

Loads environment variables, API keys, and application settings
using pydantic-settings, and configures standard Python logging.
"""

from functools import lru_cache
import logging
import sys
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# ---------------------------------------------------------------------------
# Logging Configuration
# ---------------------------------------------------------------------------
# Configure a clean console logger with timestamps and log levels.
LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

logging.basicConfig(
    level=logging.INFO,
    format=LOG_FORMAT,
    datefmt=DATE_FORMAT,
    stream=sys.stdout,
    force=True,
)

logger = logging.getLogger("nova.config")


# ---------------------------------------------------------------------------
# Application Settings
# ---------------------------------------------------------------------------
class Settings(BaseSettings):
    """Application settings loaded from environment variables and .env file."""

    # Application metadata and server configuration
    app_name: str = "Nova Support AI"
    app_env: str = "development"
    debug: bool = True
    host: str = "0.0.0.0"
    port: int = 8000

    # Google Gemini API configuration
    gemini_api_key: str = ""
    gemini_model: str = "gemini-3.5-flash-lite"

    # Provider request timeout in milliseconds.
    gemini_timeout_ms: int = Field(default=30_000, gt=0)

    # Pydantic Settings configuration.
    model_config = SettingsConfigDict(
        env_file=".env.example",
        env_file_encoding="utf-8",
        extra="ignore",
    )


# ---------------------------------------------------------------------------
# Settings Factory
# ---------------------------------------------------------------------------
@lru_cache
def get_settings() -> Settings:
    """Instantiate and cache application settings, logging safe startup info."""
    settings = Settings()

    # Log safe startup details (confirming configuration loaded without exposing secrets)
    api_key_configured = bool(
        settings.gemini_api_key and settings.gemini_api_key.strip()
    )
    logger.info(
        "Configuration loaded successfully: app_name='%s', env='%s', model='%s', debug=%s, api_key_configured=%s",
        settings.app_name,
        settings.app_env,
        settings.gemini_model,
        settings.debug,
        api_key_configured,
    )

    return settings
