from datetime import datetime, timedelta, timezone
from typing import Dict, Union

import numpy as np
from scipy import stats
from sqlalchemy.orm import Session

from .. import crud, models


class DriftDetectionService:
    def __init__(self, db: Session):
        self.db = db

    def calculate_ks_test_drift(
        self, model_id: int, window_days: int = 7
    ) -> Union[Dict, None]:
        """
        Calculates data drift for a model using the Kolmogorov-Smirnov test.
        """
        # a. Query model and verify it exists and has a baseline
        model = self.db.query(models.Model).filter(models.Model.id == model_id).first()
        if not model or model.baseline_mean is None or model.baseline_std is None:
            return None

        # b. Get predictions from the last N days
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=window_days)
        predictions = (
            self.db.query(models.Prediction)
            .filter(
                models.Prediction.model_id == model_id,
                models.Prediction.time >= cutoff_date,
            )
            .all()
        )

        # c. Return None if there are fewer than 30 predictions
        if len(predictions) < 30:
            return None

        current_values = [p.prediction_value for p in predictions]

        # d. Create a baseline distribution from the model's stored stats
        baseline_distribution = np.random.normal(
            loc=model.baseline_mean, scale=model.baseline_std, size=1000
        )

        # e. Check if current values follow a normal distribution
        _, p_value_normality = stats.shapiro(current_values)
        if p_value_normality < 0.05:
            # If not normally distributed, use Mann-Whitney U test
            ks_statistic, p_value = stats.mannwhitneyu(baseline_distribution, current_values)
        else:
            # If normally distributed, use KS test
            ks_statistic, p_value = stats.ks_2samp(baseline_distribution, current_values)

        drift_detected = p_value < 0.05

        # f. If drift is detected, create and save a DriftAlert record
        if drift_detected:
            crud.create_drift_alert(
                db=self.db,
                model_id=model_id,
                alert_type="ks_test" if p_value_normality >= 0.05 else "mannwhitneyu",
                drift_score=p_value,
                detected_at=datetime.now(timezone.utc),
            )

        # g. Always return a dictionary with the results
        return {
            "drift_detected": drift_detected,
            "drift_score": ks_statistic if p_value_normality >= 0.05 else None,
            "p_value": p_value,
            "samples": len(current_values),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
