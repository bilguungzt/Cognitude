from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .. import crud, models, schemas
from ..security import get_db, verify_api_key

router = APIRouter()


@router.post("/", response_model=schemas.Model)
def create_model(
    model: schemas.ModelCreate,
    db: Session = Depends(get_db),
    organization: models.Organization = Depends(verify_api_key),
):
    return crud.create_model(db=db, model=model, organization_id=organization.id)


@router.get("/", response_model=List[schemas.Model])
def get_models(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    organization: models.Organization = Depends(verify_api_key),
):
    return crud.get_models(
        db=db, organization_id=organization.id, skip=skip, limit=limit
    )
