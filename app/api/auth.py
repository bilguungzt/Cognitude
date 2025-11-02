from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import crud, schemas, security
from ..db.session import get_db

router = APIRouter()


@router.post("/register", response_model=schemas.OrganizationWithAPIKey, status_code=201)
def register_organization(
    *,
    db: Session = Depends(get_db),
    organization_in: schemas.OrganizationCreate,
):
    existing_organization = crud.organization.get_by_name(db=db, name=organization_in.name)
    if existing_organization:
        raise HTTPException(
            status_code=400,
            detail="An organization with this name already exists.",
        )

    api_key = security.generate_api_key()
    new_organization = crud.organization.create(db=db, obj_in=organization_in, api_key=api_key)

    return schemas.OrganizationWithAPIKey(
        id=new_organization.id,
        name=new_organization.name,
        created_at=new_organization.created_at,
        api_key=api_key,
    )