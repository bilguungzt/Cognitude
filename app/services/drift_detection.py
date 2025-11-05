from datetime import datetime, timedelta, timezone
from typing import Dict, Union

import numpy as np
from scipy import stats
from sqlalchemy.orm import Session

from .. import crud, models


class DriftDetectionService:
    def __init__(self, db: Session):
        # Initialize the service with a database session
        self.db = db

    def calculate_ks_test_drift(
        self, model_id: int, window_days: int = 7
    ) -> Union[Dict, None]:
        """
        Calculates data drift for a model using the Kolmogorov-Smirnov test.
        """
        # Query the model to ensure it exists and has baseline statistics
        model = self.db.query(models.Model).filter(models.Model.id == model_id).first()
        if not model or model.baseline_mean is None or model.baseline_std is None:
            # Return None if the model doesn't exist or lacks baseline stats
            return None

        # Calculate the cutoff date for the last N days of predictions
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=window_days)
        # Query predictions from the database within the specified time window
        predictions = (
            self.db.query(models.Prediction)
            .filter(
                models.Prediction.model_id == model_id,
                models.Prediction.time >= cutoff_date,
            )
            .all()
        )

        # Return None if there are fewer than 30 predictions to ensure statistical significance
        if len(predictions) < 30:
            return None

        # Extract prediction values from the queried predictions
        current_values = [p.prediction_value for p in predictions]

        # Create a baseline distribution using the model's stored mean and standard deviation
        baseline_distribution = np.random.normal(
            loc=model.baseline_mean, scale=model.baseline_std, size=1000
        )

        # Run the two-sample Kolmogorov-Smirnov test between the baseline and current distributions
        ks_statistic, p_value = stats.ks_2samp(baseline_distribution, current_values)

        # Determine if drift is detected based on a p-value threshold (commonly 0.05)
        drift_detected = p_value < 0.05

        # If drift is detected, create and save a DriftAlert record in the database
        if drift_detected:
            crud.create_drift_alert(
                db=self.db,
                model_id=model_id,
                alert_type="ks_test",
                drift_score=p_value,
                detected_at=datetime.now(timezone.utc),
            )

        # Return a dictionary containing the results of the drift detection
        return {
            "drift_detected": drift_detected,
            "drift_score": ks_statistic,
            "p_value": p_value,
            "samples": len(current_values),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
