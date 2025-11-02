from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from . import crud, schemas, security
from .dependencies import get_db

router = APIRouter()


@router.post("/register", response_model=schemas.OrganizationWithAPIKey)
def register_organization(
    organization: schemas.OrganizationCreate, db: Session = Depends(get_db)
):
    api_key = security.generate_api_key()
    hashed_api_key = security.get_api_key_hash(api_key)
    db_organization = crud.create_organization(
        db=db, organization=organization, hashed_api_key=hashed_api_key
    )
    return schemas.OrganizationWithAPIKey(
        id=db_organization.id,
        name=db_organization.name,
        api_key=api_key,
    )