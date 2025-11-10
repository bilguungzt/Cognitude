import hashlib
import hmac
import secrets
from os import getenv
from typing import Final

from fastapi.security import APIKeyHeader
from sqlalchemy.orm import Session
from fastapi import Depends, HTTPException, status, Security

from . import crud
from .database import SessionLocal

# Fallback salt ensures deterministic hashing if env var is unset.
_DEFAULT_SALT: Final[bytes] = b"cognitude-static-salt"


def _get_salt() -> bytes:
    configured = getenv("API_KEY_SALT")
    if configured:
        return configured.encode("utf-8")
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
    organizations = crud.get_organizations(db)
    for org in organizations:
        stored_hash = getattr(org, "api_key_hash", None)
        if stored_hash and verify_password(api_key, stored_hash):
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
