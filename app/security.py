import hashlib
import hmac
import secrets
import logging
from functools import lru_cache
from typing import Final, Optional

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


def compute_api_key_digest(api_key: str) -> str:
    """Deterministic SHA256 digest for API-key lookups."""
    return hashlib.sha256(api_key.encode("utf-8")).hexdigest()


@lru_cache(maxsize=2048)
def _cached_digest_lookup(digest: str) -> Optional[int]:
    """Cached lookup to map digests to organization IDs."""
    db = SessionLocal()
    try:
        result = db.query(models.Organization.id).filter(
            models.Organization.api_key_digest == digest
        ).first()
        return result[0] if result else None
    finally:
        db.close()


def invalidate_api_key_cache() -> None:
    _cached_digest_lookup.cache_clear()

def get_password_hash(password: str) -> str:
    """Hash a password using bcrypt for secure storage."""
    # bcrypt has a 72-byte limit, truncate if necessary
    password_bytes = password.encode('utf-8')
    if len(password_bytes) > 72:
        password = password_bytes[:72].decode('utf-8', errors='ignore')
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hashed password using bcrypt."""
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception:
        # On any unexpected error, be conservative and return False
        return False

def create_api_key() -> str:
    # Generate a token that stays within bcrypt's 72-byte limit
    # Use a simple base64 encoded random bytes for reliability
    import base64
    return base64.urlsafe_b64encode(secrets.token_bytes(16)).decode('ascii').rstrip('=')

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
    
    normalized_key = api_key.strip()
    digest = compute_api_key_digest(normalized_key)

    try:
        org = None
        cached_org_id = _cached_digest_lookup(digest)
        if cached_org_id:
            org = db.query(models.Organization).filter(
                models.Organization.id == cached_org_id
            ).first()
        if not org:
            org = db.query(models.Organization).filter(
                models.Organization.api_key_digest == digest
            ).first()

        if org and org.api_key_digest and hmac.compare_digest(org.api_key_digest, digest):
            if org.verify_api_key(normalized_key):
                return org

        # Fallback for legacy rows without digests
        organizations = crud.get_organizations(db)
        for candidate in organizations:
            stored_digest = candidate.api_key_digest
            if stored_digest:
                if hmac.compare_digest(stored_digest, digest) and candidate.verify_api_key(normalized_key):
                    return candidate
            elif candidate.verify_api_key(normalized_key):
                candidate.api_key_digest = digest
                db.commit()
                invalidate_api_key_cache()
                return candidate

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or missing API Key",
        )
    except HTTPException:
        raise
    except Exception as e:
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
    
    normalized_key = api_key.strip()
    digest = compute_api_key_digest(normalized_key)

    organizations = crud.get_organizations(db)
    for org in organizations:
        stored_digest = org.api_key_digest
        if stored_digest and hmac.compare_digest(stored_digest, digest):
            if org.verify_api_key(normalized_key):
                return org
        elif stored_digest is None and org.verify_api_key(normalized_key):
            org.api_key_digest = digest
            db.commit()
            invalidate_api_key_cache()
            return org

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Could not validate credentials",
    )
