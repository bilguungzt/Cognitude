from typing import List, Dict, Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import crud, models, schemas
from ..security import get_db, get_organization_from_api_key

router = APIRouter()


@router.post("/", response_model=schemas.Model)
def create_model(
    model: schemas.ModelCreate,
    organization: models.Organization = Depends(get_organization_from_api_key),
    db: Session = Depends(get_db),
):
    return crud.create_model(db=db, model=model, organization_id=organization.id)


@router.get("/", response_model=List[schemas.Model])
def get_models(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    organization: models.Organization = Depends(get_organization_from_api_key),
):
    return crud.get_models(
        db=db, organization_id=organization.id, skip=skip, limit=limit
    )


@router.put("/{model_id}/features/{feature_id}")
def update_feature_baseline_stats(
    model_id: int,
    feature_id: int,
    baseline_stats: Dict[str, Any],
    organization: models.Organization = Depends(get_organization_from_api_key),
    db: Session = Depends(get_db),
):
    """Update the baseline_stats for a model feature."""
    # Get the model feature
    feature = (
        db.query(models.ModelFeature)
        .join(models.Model)
        .filter(
            models.ModelFeature.id == feature_id,
            models.Model.id == model_id,
            models.Model.organization_id == organization.id,  # type: ignore
        )
        .first()
    )
    
    if not feature:
        raise HTTPException(status_code=404, detail="Feature not found")
    
    # Update baseline_stats
    feature.baseline_stats = baseline_stats.get("baseline_stats")  # type: ignore
    db.commit()
    db.refresh(feature)
    
    return {"success": True, "feature_id": feature_id}
