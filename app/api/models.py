from typing import List, Dict, Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import crud, models, schemas
from ..security import get_db, get_organization_from_api_key

router = APIRouter()


@router.post(
    "/", 
    response_model=schemas.Model,
    summary="Register a new model",
    description="""
    Register a new ML model for drift monitoring.
    
    Define your model's features so DriftAssure can track drift per-feature.
    
    **Example:**
    ```bash
    curl -X POST http://localhost:8000/models/ \\
      -H "X-API-Key: your-api-key" \\
      -H "Content-Type: application/json" \\
      -d '{
        "name": "fraud_detector_v1",
        "version": "1.0.0",
        "description": "Credit card fraud detection model",
        "features": [
          {"feature_name": "transaction_amount", "feature_type": "numeric", "order": 1},
          {"feature_name": "merchant_category", "feature_type": "categorical", "order": 2}
        ]
      }'
    ```
    """,
    responses={
        200: {
            "description": "Model created successfully",
            "content": {
                "application/json": {
                    "example": {
                        "name": "fraud_detector_v1",
                        "version": "1.0.0",
                        "description": "Credit card fraud detection model",
                        "id": 1,
                        "organization_id": 1,
                        "created_at": "2025-11-06T04:48:08.472638Z",
                        "updated_at": "2025-11-06T04:48:08.472638Z",
                        "features": [
                            {
                                "feature_name": "transaction_amount",
                                "feature_type": "numeric",
                                "order": 1,
                                "id": 1,
                                "model_id": 1
                            }
                        ]
                    }
                }
            }
        }
    }
)
def create_model(
    model: schemas.ModelCreate,
    organization: models.Organization = Depends(get_organization_from_api_key),
    db: Session = Depends(get_db),
):
    return crud.create_model(db=db, model=model, organization_id=organization.id)


@router.get(
    "/", 
    response_model=List[schemas.Model],
    summary="List all models",
    description="""
    List all models registered by your organization.
    
    Supports pagination with `skip` and `limit` parameters.
    """,
    responses={
        200: {
            "description": "List of models",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "name": "fraud_detector_v1",
                            "version": "1.0.0",
                            "id": 1,
                            "organization_id": 1,
                            "features": []
                        }
                    ]
                }
            }
        }
    }
)
def get_models(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    organization: models.Organization = Depends(get_organization_from_api_key),
):
    return crud.get_models(
        db=db, organization_id=organization.id, skip=skip, limit=limit
    )


@router.get(
    "/{model_id}",
    response_model=schemas.Model,
    summary="Get a single model by ID",
    description="""
    Get detailed information about a specific model including all its features.
    """,
    responses={
        200: {
            "description": "Model details",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "name": "fraud_detector_v1",
                        "version": "1.0.0",
                        "description": "Detects fraudulent transactions",
                        "organization_id": 1,
                        "created_at": "2025-11-05T10:00:00Z",
                        "updated_at": "2025-11-05T10:00:00Z",
                        "features": [
                            {
                                "id": 1,
                                "feature_name": "amount",
                                "feature_type": "numeric",
                                "order": 1
                            }
                        ]
                    }
                }
            }
        },
        404: {
            "description": "Model not found",
            "content": {
                "application/json": {
                    "example": {"detail": "Model not found"}
                }
            }
        }
    }
)
def get_model_by_id(
    model_id: int,
    db: Session = Depends(get_db),
    organization: models.Organization = Depends(get_organization_from_api_key),
):
    """Get a single model by ID."""
    db_model = crud.get_model(db, model_id=model_id)
    if not db_model:
        raise HTTPException(status_code=404, detail="Model not found")
    if db_model.organization_id != organization.id:  # type: ignore
        raise HTTPException(status_code=404, detail="Model not found")
    return db_model


@router.put(
    "/{model_id}/features/{feature_id}",
    summary="Update feature baseline statistics",
    description="""
    Update the baseline statistics for a model feature.
    
    Baseline stats are used as the reference distribution for drift detection.
    You should set these after logging your initial batch of "good" predictions.
    
    **Example:**
    ```bash
    curl -X PUT http://localhost:8000/models/1/features/1 \\
      -H "X-API-Key: your-api-key" \\
      -H "Content-Type: application/json" \\
      -d '{
        "baseline_stats": {
          "samples": [0.5, 0.52, 0.48, 0.51, ...]
        }
      }'
    ```
    
    The `samples` array should contain 50-100 prediction values from your baseline period.
    """,
    responses={
        200: {
            "description": "Baseline stats updated successfully",
            "content": {
                "application/json": {
                    "example": {"success": True, "feature_id": 1}
                }
            }
        },
        404: {
            "description": "Feature not found",
            "content": {
                "application/json": {
                    "example": {"detail": "Feature not found"}
                }
            }
        }
    }
)
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


@router.post(
    "/{model_id}/baseline",
    summary="Auto-generate baseline from existing predictions",
    description="""
    Automatically generate baseline statistics from existing predictions.
    
    This endpoint will:
    1. Fetch all existing predictions for the model
    2. Calculate baseline statistics (using prediction_value as samples)
    3. Update all features with the same baseline
    
    Use this as a quick way to set up a baseline after logging initial predictions.
    """,
    responses={
        200: {
            "description": "Baseline generated successfully",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "predictions_count": 100,
                        "features_updated": 3
                    }
                }
            }
        },
        404: {
            "description": "Model not found or no predictions available",
        }
    }
)
def auto_generate_baseline(
    model_id: int,
    organization: models.Organization = Depends(get_organization_from_api_key),
    db: Session = Depends(get_db),
):
    """Auto-generate baseline stats from existing predictions."""
    # Get the model
    db_model = crud.get_model(db, model_id=model_id)
    if not db_model:
        raise HTTPException(status_code=404, detail="Model not found")
    
    if db_model.organization_id != organization.id:  # type: ignore
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Get all predictions
    predictions = (
        db.query(models.Prediction)
        .filter(models.Prediction.model_id == model_id)
        .all()
    )
    
    if len(predictions) < 30:
        raise HTTPException(
            status_code=400,
            detail=f"Need at least 30 predictions to generate baseline. Found: {len(predictions)}"
        )
    
    # Extract prediction values
    samples = [p.prediction_value for p in predictions]
    
    # Update all features with the same baseline
    features = (
        db.query(models.ModelFeature)
        .filter(models.ModelFeature.model_id == model_id)
        .all()
    )
    
    features_updated = 0
    for feature in features:
        feature.baseline_stats = {"samples": samples}  # type: ignore
        features_updated += 1
    
    db.commit()
    
    return {
        "success": True,
        "predictions_count": len(predictions),
        "features_updated": features_updated
    }
