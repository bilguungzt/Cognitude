from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import crud, schemas, security
from ..security import get_db

router = APIRouter()

@router.post(
    "/models/{model_id}/predictions", 
    response_model=List[schemas.Prediction],
    summary="Log predictions",
    description="""
    Log one or more predictions for drift monitoring.
    
    Send predictions in real-time or batch. Each prediction should include:
    - `features`: Dictionary of feature name → value
    - `prediction_value`: The model's output (float)
    - `actual_value` (optional): Ground truth for later analysis
    - `timestamp` (optional): When the prediction was made (defaults to now)
    
    **Example (Single Prediction):**
    ```bash
    curl -X POST https://api.cognitude.io/predictions/models/1/predictions \\
      -H "X-API-Key: your-api-key" \\
      -H "Content-Type: application/json" \\
      -d '[{
        "features": {"transaction_amount": 150.0, "merchant_category": "grocery"},
        "prediction_value": 0.05,
        "actual_value": 0.0,
        "timestamp": "2025-11-06T10:30:00Z"
      }]'
    ```
    
    **Example (Batch):**
    ```bash
    curl -X POST https://api.cognitude.io/predictions/models/1/predictions \\
      -H "X-API-Key: your-api-key" \\
      -H "Content-Type: application/json" \\
      -d '[
        {"features": {"amount": 100}, "prediction_value": 0.02},
        {"features": {"amount": 200}, "prediction_value": 0.15},
        {"features": {"amount": 50}, "prediction_value": 0.01}
      ]'
    ```
    
    Drift detection runs automatically every 15 minutes on logged predictions.
    """,
    responses={
        200: {
            "description": "Predictions logged successfully",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "id": 1,
                            "model_id": 1,
                            "prediction_value": 0.05,
                            "actual_value": 0.0,
                            "time": "2025-11-06T10:30:00Z"
                        }
                    ]
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
        },
        403: {
            "description": "Not authorized to use this model",
            "content": {
                "application/json": {
                    "example": {"detail": "Not authorized to use this model"}
                }
            }
        }
    }
)
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
