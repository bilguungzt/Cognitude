from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .. import crud, models, schemas
from .dependencies import get_current_organization, get_db

router = APIRouter()


@router.post(
    "/models/{model_id}/predictions",
    response_model=schemas.Prediction,
    status_code=status.HTTP_201_CREATED,
)
def create_prediction_for_model(
    model_id: int,
    prediction: schemas.PredictionCreate,
    db: Session = Depends(get_db),
    current_organization: models.Organization = Depends(get_current_organization),
):
    db_model = crud.get_model(db, model_id=model_id)
    if not db_model or db_model.organization_id != current_organization.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this model",
        )
    return crud.create_prediction(db=db, prediction=prediction, model_id=model_id)