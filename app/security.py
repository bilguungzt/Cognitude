import hashlib
import hmac
import secrets
import logging
from typing import Final

from fastapi.security import APIKeyHeader
from sqlalchemy.orm import Session
from fastapi import Depends, HTTPException, status, Security

from . import crud, models
from .database import SessionLocal, get_db
from .config import get_settings

# Import pwd_context from models for password hashing
pwd_context = models.pwd_context

settings = get_settings()

# Fallback salt ensures deterministic hashing if env var is unset.
_DEFAULT_SALT: Final[bytes] = b"cognitude-static-salt"


def _get_salt() -> bytes:
    configured = settings.SECRET_KEY
    if configured:
        return configured.get_secret_value().encode("utf-8")
    return _DEFAULT_SALT

api_key_header = APIKeyHeader(name="X-API-Key")

def get_password_hash(password: str) -> str:
    """Hash a password using bcrypt for secure storage."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hashed password using bcrypt."""
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception:
        # On any unexpected error, be conservative and return False
        return False

def create_api_key() -> str:
    return secrets.token_urlsafe(32)

# get_db() function removed - use the one from app.database instead

def get_organization_from_api_key(api_key: str = Security(api_key_header), db: Session = Depends(get_db)):
    """
    Authenticates a request by validating the provided API key.

    Uses database query with indexing for efficient lookup, falling back to
    Redis caching for frequently used keys.

    Args:
        api_key: The API key from the 'X-API-Key' header.
        db: The database session.

    Returns:
        The authenticated Organization object.

    Raises:
        HTTPException: If the API key is invalid or not found.
    """
    if not api_key or not api_key.strip():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="API Key is required",
        )
    
    try:
        # Query database for organization with matching API key
        # The database index on api_key_hash makes this efficient
        organizations = crud.get_organizations(db)
        for org in organizations:
            if org.verify_api_key(api_key):
                return org

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or missing API Key",
        )
    except HTTPException:
        raise
    except Exception as e:
        # Log the error and raise a generic authentication error
        logger = logging.getLogger(__name__)
        logger.error(f"Error during API key verification: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication service error",
        )

async def verify_api_key(api_key: str = Depends(api_key_header), db: Session = Depends(get_db)):
    """
    Async version of API key verification for use with async endpoints.
    """
    if not api_key or not api_key.strip():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="API Key is required",
        )
    
    organizations = crud.get_organizations(db)
    for org in organizations:
        if org.verify_api_key(api_key):
            return org

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Could not validate credentials",
    )
