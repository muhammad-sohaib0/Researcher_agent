"""
Configuration Management Module

Uses pydantic-settings for environment variable handling.
Supports both .env file and system environment variables.
"""

import os
from pathlib import Path
from typing import List, Optional
from functools import lru_cache

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with pydantic-settings."""

    # Application
    app_name: str = "Research Agent API"
    app_version: str = "1.0.0"
    debug: bool = False

    # Database
    database_url: str = "sqlite:///./research_agent.db"
    database_echo: bool = False

    # JWT Authentication
    jwt_secret_key: str = Field(default="your-secret-key-change-in-production")
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24 * 7  # 7 days

    # API Keys
    gemini_api_key_1: Optional[SecretStr] = None
    gemini_api_key_2: Optional[SecretStr] = None
    gemini_api_key_3: Optional[SecretStr] = None
    gemini_api_key_4: Optional[SecretStr] = None
    groq_api_key: Optional[SecretStr] = None

    # CORS
    allowed_origins: List[str] = Field(
        default=["http://localhost:3000", "http://127.0.0.1:3000"]
    )

    # Redis (for caching)
    redis_url: Optional[str] = None
    redis_enabled: bool = False

    # Rate Limiting
    rate_limit_requests: int = 100
    rate_limit_window_seconds: int = 60

    # File Upload
    max_file_size_mb: int = 100
    upload_dir: str = "./uploads"
    downloads_dir: str = "./downloads"

    # Logging
    log_level: str = "INFO"
    log_format: str = "json"

    model_config = SettingsConfigDict(
        env_file=Path(__file__).parent.parent.parent / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.

    Using lru_cache ensures settings are loaded only once
    and reused throughout the application lifecycle.
    """
    return Settings()


# Convenience function to get API keys safely
def get_api_key(key_name: str) -> Optional[str]:
    """Get API key from settings, returns None if not set."""
    settings = get_settings()
    api_key = getattr(settings, key_name, None)
    if api_key:
        return api_key.get_secret_value()
    return None
