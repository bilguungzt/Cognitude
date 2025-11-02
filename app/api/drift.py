from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import crud
from .. import security
from ..security import get_db

router = APIRouter()

@router.get(
    "/models/{model_id}/drift/current",
    dependencies=[Depends(security.verify_api_key)],
)
def get_current_drift(model_id: int, db: Session = Depends(get_db)):
    db_model = crud.get_model(db, model_id=model_id)
    if not db_model:
        raise HTTPException(status_code=404, detail="Model not found")

    if db_model.baseline_mean is None or db_model.baseline_stdev is None:
        raise HTTPException(
            status_code=400,
            detail="Model does not have a calculated baseline for drift detection."
        )

    predictions = crud.get_latest_predictions(db=db, model_id=model_id, limit=100)

    if not predictions:
        raise HTTPException(
            status_code=404,
            detail="No recent predictions found to calculate current drift."
        )

    prediction_values = [p.prediction for p in predictions]
    current_mean = sum(prediction_values) / len(prediction_values)

    baseline_mean = db_model.baseline_mean
    baseline_stdev = db_model.baseline_stdev

    drift_detected = abs(current_mean - baseline_mean) > (2 * baseline_stdev)

    return {
        "current_mean": current_mean,
        "baseline_mean": baseline_mean,
        "drift_detected": drift_detected,
    }
