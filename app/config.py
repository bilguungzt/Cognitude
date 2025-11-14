from functools import lru_cache
from typing import Optional, List
from pydantic import SecretStr
from typing import Any
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
    # Use plain strings here to allow flexible URLs in local/dev environments
    DATABASE_URL: Optional[str] = None
    REDIS_URL: Optional[str] = None

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
    
    # Application settings
    APP_NAME: str = "Cognitude LLM Proxy"
    APP_VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Rate limiting defaults
    RATE_LIMIT_PER_MINUTE: int = 100
    RATE_LIMIT_PER_HOUR: int = 3000
    RATE_LIMIT_PER_DAY: int = 50000
    
    # Cache settings
    CACHE_TTL_HOURS: int = 24
    CACHE_MAX_SIZE_KB: int = 100
    
    # Model settings
    MAX_TOKENS_PER_REQUEST: int = 4096
    MAX_MESSAGE_SIZE_KB: int = 50
    MAX_TOTAL_MESSAGE_SIZE_KB: int = 100
    
    # Alert settings
    ALERT_DASHBOARD_URL: str = "http://your-server:8000"
    ALERT_ANALYTICS_PATH: str = "/analytics/usage"
    ALERT_RECOMMENDATIONS_PATH: str = "/analytics/recommendations"
    
    # Allowed providers
    ALLOWED_PROVIDERS: List[str] = ["openai", "anthropic", "cohere", "google", "azure", "huggingface"]
    
    # Model characteristics (can be overridden via environment)
    MODEL_COST_MULTIPLIER: float = 1.0


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