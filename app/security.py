import secrets

from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import APIKeyHeader
from sqlalchemy.orm import Session

from . import crud
from .database import SessionLocal

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

api_key_header = APIKeyHeader(name="X-API-Key")

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

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
        if org.api_key_hash and pwd_context.verify(api_key, org.api_key_hash):
            return org

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Could not validate credentials",
    )
