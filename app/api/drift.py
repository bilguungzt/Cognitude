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
    curl https://api.driftassure.com/drift/models/1/drift/current \\
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


@router.get(
    "/models/{model_id}/history",
    summary="Get drift history",
    description="""
    Retrieve historical drift detection results for a model.
    
    Returns a time-series of drift scores, p-values, and detection status.
    Useful for visualizing drift trends over time.
    
    **Query Parameters:**
    - `limit`: Maximum number of records to return (default: 100)
    - `days`: Number of days to look back (default: 30)
    
    **Example:**
    ```bash
    curl https://api.driftassure.com/drift/models/1/history?limit=50&days=14 \\
      -H "X-API-Key: your-api-key"
    ```
    """,
    responses={
        200: {
            "description": "Drift history records",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "timestamp": "2025-11-05T10:30:00Z",
                            "drift_detected": True,
                            "drift_score": 0.65,
                            "p_value": 0.012,
                            "samples": 150
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
        }
    }
)
def get_drift_history(
    model_id: int,
    limit: int = 100,
    days: int = 30,
    db: Session = Depends(get_db),
    organization: models.Organization = Depends(security.verify_api_key),
):
    """Get historical drift detection results for a model."""
    # Verify model exists and belongs to organization
    db_model = crud.get_model(db, model_id=model_id)
    if not db_model:
        raise HTTPException(status_code=404, detail="Model not found")
    # Type ignore for SQLAlchemy comparison
    if db_model.organization_id != organization.id:  # type: ignore
        raise HTTPException(status_code=404, detail="Model not found")
    
    # Calculate cutoff date
    from datetime import datetime, timedelta, timezone
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
    
    # Query drift history
    history = (
        db.query(models.DriftHistory)
        .filter(
            models.DriftHistory.model_id == model_id,
            models.DriftHistory.timestamp >= cutoff_date
        )
        .order_by(models.DriftHistory.timestamp.desc())
        .limit(limit)
        .all()
    )
    
    # Format response
    return [
        {
            "timestamp": record.timestamp.isoformat(),
            "drift_detected": record.drift_detected,
            "drift_score": record.drift_score,
            "p_value": record.p_value,
            "samples": record.samples
        }
        for record in reversed(history)  # Return oldest first for chart display
    ]


@router.get(
    "/alerts",
    summary="Get all drift alerts",
    description="""
    Retrieve all drift alerts across all models for your organization.
    
    Drift alerts are automatically created when drift is detected (p < 0.05).
    Each alert includes the model, drift score, and timestamp.
    
    **Query Parameters:**
    - `limit`: Maximum number of alerts to return (default: 100)
    - `days`: Number of days to look back (default: 30)
    
    **Example:**
    ```bash
    curl https://api.driftassure.com/drift/alerts?limit=50 \\
      -H "X-API-Key: your-api-key"
    ```
    
    **Response:**
    ```json
    [
      {
        "id": 123,
        "model_id": 1,
        "model_name": "fraud_detector_v1",
        "alert_type": "data_drift",
        "drift_score": 0.678,
        "detected_at": "2025-11-06T10:30:00Z"
      }
    ]
    ```
    """,
    responses={
        200: {
            "description": "List of drift alerts",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "id": 123,
                            "model_id": 1,
                            "model_name": "fraud_detector_v1",
                            "alert_type": "data_drift",
                            "drift_score": 0.678,
                            "detected_at": "2025-11-06T10:30:00Z"
                        }
                    ]
                }
            }
        }
    }
)
def get_drift_alerts(
    limit: int = 100,
    days: int = 30,
    db: Session = Depends(get_db),
    organization: models.Organization = Depends(security.verify_api_key),
):
    """Get all drift alerts for the organization."""
    from datetime import datetime, timedelta, timezone
    
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
    
    # Query drift alerts with model information
    alerts = (
        db.query(models.DriftAlert, models.Model.name)
        .join(models.Model, models.DriftAlert.model_id == models.Model.id)
        .filter(
            models.Model.organization_id == organization.id,  # type: ignore
            models.DriftAlert.detected_at >= cutoff_date
        )
        .order_by(models.DriftAlert.detected_at.desc())
        .limit(limit)
        .all()
    )
    
    # Format response
    return [
        {
            "id": alert.id,
            "model_id": alert.model_id,
            "model_name": model_name,
            "alert_type": alert.alert_type,
            "drift_score": alert.drift_score,
            "detected_at": alert.detected_at.isoformat()
        }
        for alert, model_name in alerts
    ]


@router.get(
    "/models/{model_id}/alerts",
    summary="Get drift alerts for a specific model",
    description="""
    Retrieve drift alerts for a specific model.
    
    **Query Parameters:**
    - `limit`: Maximum number of alerts to return (default: 100)
    - `days`: Number of days to look back (default: 30)
    
    **Example:**
    ```bash
    curl https://api.driftassure.com/drift/models/1/alerts?limit=20 \\
      -H "X-API-Key: your-api-key"
    ```
    """,
    responses={
        200: {
            "description": "List of drift alerts for the model",
        },
        404: {
            "description": "Model not found"
        }
    }
)
def get_model_drift_alerts(
    model_id: int,
    limit: int = 100,
    days: int = 30,
    db: Session = Depends(get_db),
    organization: models.Organization = Depends(security.verify_api_key),
):
    """Get drift alerts for a specific model."""
    # Verify model exists and belongs to organization
    db_model = crud.get_model(db, model_id=model_id)
    if not db_model:
        raise HTTPException(status_code=404, detail="Model not found")
    if db_model.organization_id != organization.id:  # type: ignore
        raise HTTPException(status_code=404, detail="Model not found")
    
    from datetime import datetime, timedelta, timezone
    
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
    
    # Query drift alerts for this model
    alerts = (
        db.query(models.DriftAlert)
        .filter(
            models.DriftAlert.model_id == model_id,
            models.DriftAlert.detected_at >= cutoff_date
        )
        .order_by(models.DriftAlert.detected_at.desc())
        .limit(limit)
        .all()
    )
    
    # Format response
    return [
        {
            "id": alert.id,
            "model_id": alert.model_id,
            "alert_type": alert.alert_type,
            "drift_score": alert.drift_score,
            "detected_at": alert.detected_at.isoformat()
        }
        for alert in alerts
    ]
