from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .. import crud, schemas
from ..auth import get_current_organization
from ..database import get_db

router = APIRouter()


@router.post("/models", response_model=schemas.Model, status_code=201)
def create_model(
    model: schemas.ModelCreate,
    db: Session = Depends(get_db),
    current_organization: schemas.Organization = Depends(get_current_organization),
):
    return crud.create_model_for_organization(
        db=db, model=model, organization_id=current_organization.id
    )


@router.get("/models", response_model=list[schemas.Model])
def read_models(
    db: Session = Depends(get_db),
    current_organization: schemas.Organization = Depends(get_current_organization),
):
    return crud.get_models_by_organization(
        db=db, organization_id=current_organization.id
    )