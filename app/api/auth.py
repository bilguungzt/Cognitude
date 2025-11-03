from typing import cast

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .. import crud, schemas, security
from ..security import get_db

router = APIRouter()


@router.post("/register", response_model=schemas.OrganizationWithAPIKey)
def register_organization(
    organization: schemas.OrganizationCreate, db: Session = Depends(get_db)
):
    api_key = security.create_api_key()
    hashed_api_key = security.get_password_hash(api_key)
    try:
        db_organization = crud.create_organization(
            db=db, organization=organization, api_key_hash=hashed_api_key
        )
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Organization name already exists.",
        ) from exc
    else:
        return schemas.OrganizationWithAPIKey(
            id=cast(int, db_organization.id),
            name=cast(str, db_organization.name),
            api_key=api_key,
        )
