import hashlib
import hmac
import secrets
from typing import Final

from fastapi.security import APIKeyHeader
from sqlalchemy.orm import Session
from fastapi import Depends, HTTPException, status, Security

from . import crud
from .database import SessionLocal
from .config import get_settings

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
    # Temporarily returning plain text password
    return password


def verify_password(plain_password: str, hashed_password: str) -> bool:
    # Simple string comparison for now
    return plain_password == hashed_password

def create_api_key() -> str:
    return secrets.token_urlsafe(32)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_organization_from_api_key(api_key: str = Security(api_key_header), db: Session = Depends(get_db)):
    """
    Authenticates a request by validating the provided API key.

    This function iterates through all organizations and uses a secure bcrypt
    verification to check the API key. This approach is necessary because
    bcrypt hashes are salted and cannot be directly looked up.

    Args:
        api_key: The API key from the 'X-API-Key' header.
        db: The database session.

    Returns:
        The authenticated Organization object.

    Raises:
        HTTPException: If the API key is invalid or not found.
    """
    organizations = crud.get_organizations(db)
    for org in organizations:
        if org.verify_api_key(api_key):
            return org

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Invalid or missing API Key",
    )

async def verify_api_key(api_key: str = Depends(api_key_header), db: Session = Depends(get_db)):
    organizations = crud.get_organizations(db)
    for org in organizations:
        stored_hash = getattr(org, "api_key_hash", None)
        if stored_hash and verify_password(api_key, stored_hash):
            return org

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Could not validate credentials",
    )
