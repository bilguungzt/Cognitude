from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import crud, models
from .. import security
from ..security import get_db
from ..services.drift_detection import DriftDetectionService

router = APIRouter()


@router.get(
    "/models/{model_id}/drift/current",
)
def get_current_drift(
    model_id: int,
    db: Session = Depends(get_db),
    organization: models.Organization = Depends(security.verify_api_key),
):
    db_model = crud.get_model(db, model_id=model_id)
    if not db_model or db_model.organization_id != organization.id:
        raise HTTPException(status_code=404, detail="Model not found")

    drift_service = DriftDetectionService(db)
    drift_results = drift_service.calculate_ks_test_drift(model_id=model_id)

    if drift_results is None:
        return {
            "drift_detected": False,
            "message": "Not enough recent prediction data to calculate drift, or model baseline is not set. At least 30 predictions are needed in the last 7 days."
        }

    return drift_results
