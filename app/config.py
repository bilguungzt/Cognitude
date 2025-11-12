from functools import lru_cache
from typing import Optional
from pydantic import SecretStr, PostgresDsn, RedisDsn
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """
    Manages application settings and environment variables.
    """
    # Core application settings
    APP_NAME: str = "Cognitude MVP"
    DEBUG: bool = False
    SECRET_KEY: Optional[SecretStr] = None

    # Database configurations
    DATABASE_URL: Optional[PostgresDsn] = None
    REDIS_URL: Optional[RedisDsn] = None

    # Security and JWT settings
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    ALGORITHM: str = "HS256"

    # Email settings
    SMTP_USERNAME: Optional[str] = None
    SMTP_PASSWORD: Optional[SecretStr] = None
    FROM_EMAIL: Optional[str] = None
    SMTP_SERVER: Optional[str] = None
    SMTP_PORT: Optional[int] = None

    # API Keys
    OPENAI_API_KEY: Optional[SecretStr] = None
    ANTHROPIC_API_KEY: Optional[SecretStr] = None
    ENVIRONMENT: Optional[str] = None
    SENTRY_DSN: Optional[str] = None


    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

@lru_cache()
def get_settings() -> Settings:
    """
    Returns a cached instance of the application settings.
    Utilizes lru_cache to ensure settings are loaded only once.
    """
    return Settings()