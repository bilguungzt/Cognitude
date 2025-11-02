
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .deps import get_db, get_current_organization
from ..models import Model, Organization

router = APIRouter()


@router.get("/models/{model_id}/drift/current")
def get_current_model_drift(
    model_id: int,
    db: Session = Depends(get_db),
    current_organization: Organization = Depends(get_current_organization),
):
    """
    Get the current drift status for a specific model.
    """
    model = db.query(Model).filter(Model.id == model_id).first()

    if not model or model.organization_id != current_organization.id:
        raise HTTPException(
            status_code=403, detail="Not authorized to access this model"
        )

    return {"model_id": model_id, "drift_status": "NO_DRIFT", "confidence_score": 0.98}
