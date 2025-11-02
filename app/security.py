
import secrets

from fastapi import Depends, HTTPException, status
from fastapi.security import APIKeyHeader
from sqlalchemy.orm import Session

from . import crud, models
from .database import get_db

api_key_header = APIKeyHeader(name="X-API-Key")


def generate_api_key() -> str:
    return secrets.token_urlsafe(32)


def get_current_organization(
    api_key: str = Depends(api_key_header), db: Session = Depends(get_db)
) -> models.Organization:
    organization = crud.get_organization_by_api_key(db, api_key=api_key)
    if not organization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API Key",
        )
    return organization
