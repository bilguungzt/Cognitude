import hashlib
import hmac
import secrets
from os import getenv
from typing import Final

from fastapi.security import APIKeyHeader
from sqlalchemy.orm import Session
from fastapi import Depends, HTTPException, status

from . import crud
from .database import SessionLocal

# Fallback salt ensures deterministic hashing if env var is unset.
_DEFAULT_SALT: Final[bytes] = b"driftguard-static-salt"


def _get_salt() -> bytes:
    configured = getenv("API_KEY_SALT")
    if configured:
        return configured.encode("utf-8")
    return _DEFAULT_SALT

api_key_header = APIKeyHeader(name="X-API-Key")

def get_password_hash(password: str) -> str:
    salt = _get_salt()
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 200000)
    return digest.hex()


def verify_password(password: str, password_hash: str) -> bool:
    expected = get_password_hash(password)
    # Use constant-time comparison to avoid timing attacks.
    return hmac.compare_digest(expected, password_hash)

def create_api_key() -> str:
    return secrets.token_urlsafe(32)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

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
