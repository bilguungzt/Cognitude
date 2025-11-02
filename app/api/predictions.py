from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from . import crud, schemas, security

router = APIRouter()

@router.post("/models/{model_id}/predictions", response_model=schemas.Prediction)
def create_prediction(
    model_id: int,
    prediction: schemas.PredictionCreate,
    db: Session = Depends(crud.get_db_session),
    current_org: schemas.Organization = Depends(security.verify_api_key),
):
    db_model = crud.get_model(db, model_id=model_id)
    if not db_model:
        raise HTTPException(status_code=404, detail="Model not found")

    if db_model.organization_id != current_org.id:
        raise HTTPException(status_code=403, detail="Not authorized to use this model")

    return crud.create_prediction(db=db, prediction=prediction, model_id=model_id)