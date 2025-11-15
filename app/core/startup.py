from typing import List

from app.config import Settings


def validate_environment(settings: Settings) -> None:
    """
    Validate that critical environment configuration is present before the app starts.
    """
    missing: List[str] = []

    if not settings.SECRET_KEY:
        missing.append("SECRET_KEY")

    environment = (settings.ENVIRONMENT or "development").lower()
    if environment in {"production", "staging"} and not settings.DATABASE_URL:
        missing.append("DATABASE_URL")

    if missing:
        missing_vars = ", ".join(missing)
        raise RuntimeError(
            f"Missing required environment variables: {missing_vars}. "
            "Set these values before starting the application."
        )

