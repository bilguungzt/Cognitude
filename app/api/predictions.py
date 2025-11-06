from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import crud, schemas, security
from ..security import get_db

router = APIRouter()

@router.post("/models/{model_id}/predictions", response_model=List[schemas.Prediction])
def log_predictions(
    model_id: int,
    predictions: List[schemas.PredictionData],
    db: Session = Depends(get_db),
    current_org: schemas.Organization = Depends(security.verify_api_key),
):
    db_model = crud.get_model(db, model_id=model_id)
    if not db_model:
        raise HTTPException(status_code=404, detail="Model not found")

    if getattr(db_model, "organization_id") != getattr(current_org, "id"):
        raise HTTPException(status_code=403, detail="Not authorized to use this model")

    if not predictions:
        return []

    db_predictions = []
    try:
        for prediction_payload in predictions:
            db_predictions.append(
                crud.create_prediction(db=db, prediction=prediction_payload, model_id=model_id)
            )

        db.commit()

        for logged_prediction in db_predictions:
            db.refresh(logged_prediction)
    except Exception:
        db.rollback()
        raise

    return db_predictions
