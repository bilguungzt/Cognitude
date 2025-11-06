from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import crud, models
from .. import security
from ..security import get_db
from ..services.drift_detection import DriftDetectionService

router = APIRouter()


@router.get(
    "/models/{model_id}/drift/current",
    summary="Check current drift status",
    description="""
    Get the current drift status for a model using the Kolmogorov-Smirnov test.
    
    Compares predictions from the last 7 days against the baseline distribution.
    Returns drift score (0-1) and whether drift was detected (p < 0.05).
    
    **Interpretation:**
    - `drift_detected: true` = Statistically significant drift (p < 0.05)
    - `drift_score`: Higher values (0.5+) indicate stronger drift
    - `p_value`: Statistical significance (< 0.05 = drift detected)
    
    **Example:**
    ```bash
    curl http://localhost:8000/drift/models/1/drift/current \\
      -H "X-API-Key: your-api-key"
    ```
    
    **Response (No Drift):**
    ```json
    {
      "drift_detected": false,
      "drift_score": 0.123,
      "p_value": 0.342,
      "samples": 150,
      "timestamp": "2025-11-06T10:30:00Z"
    }
    ```
    
    **Response (Drift Detected):**
    ```json
    {
      "drift_detected": true,
      "drift_score": 0.678,
      "p_value": 0.001,
      "samples": 200,
      "timestamp": "2025-11-06T10:30:00Z"
    }
    ```
    
    **Requirements:**
    - Model must have baseline statistics configured
    - At least 30 predictions in the last 7 days
    
    If requirements aren't met, returns a message explaining what's needed.
    """,
    responses={
        200: {
            "description": "Drift analysis results",
            "content": {
                "application/json": {
                    "examples": {
                        "drift_detected": {
                            "summary": "Drift Detected",
                            "value": {
                                "drift_detected": True,
                                "drift_score": 0.678,
                                "p_value": 0.001,
                                "samples": 200,
                                "timestamp": "2025-11-06T10:30:00Z"
                            }
                        },
                        "no_drift": {
                            "summary": "No Drift",
                            "value": {
                                "drift_detected": False,
                                "drift_score": 0.123,
                                "p_value": 0.342,
                                "samples": 150,
                                "timestamp": "2025-11-06T10:30:00Z"
                            }
                        },
                        "insufficient_data": {
                            "summary": "Not Enough Data",
                            "value": {
                                "drift_detected": False,
                                "message": "Not enough recent prediction data to calculate drift, or model baseline is not set. At least 30 predictions are needed in the last 7 days."
                            }
                        }
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
