from datetime import datetime, timedelta, timezone
from typing import Dict, Union
import asyncio

import numpy as np
from scipy import stats
from sqlalchemy.orm import Session

from .. import crud, models
from .notifications import NotificationService


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
        if not model:
            return None
            
        # Check if model has baseline samples
        baseline_features = [f for f in model.features if f.baseline_stats and 'samples' in f.baseline_stats]
        if not baseline_features:
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

        # d. Create baseline distribution from actual historical data
        # Using the first feature's baseline samples as the baseline distribution
        baseline_feature = baseline_features[0]
        baseline_distribution = np.array(baseline_feature.baseline_stats['samples'])

        # e. Run KS test (Kolmogorov-Smirnov two-sample test)
        statistic, pvalue = stats.ks_2samp(baseline_distribution, current_values)  # type: ignore
        ks_statistic = float(statistic)
        p_value = float(pvalue)

        drift_detected = p_value < 0.05

        # f. If drift is detected, create and save a DriftAlert record
        if drift_detected:
            crud.create_drift_alert(
                db=self.db,
                model_id=model_id,
                alert_type="data_drift",
                drift_score=ks_statistic,
                detected_at=datetime.now(timezone.utc),
            )
            
            # Send notifications through all active channels
            notification_service = NotificationService(self.db)
            
            # Get all active alert channels for this model's organization
            alert_channels = (
                self.db.query(models.AlertChannel)
                .filter(
                    models.AlertChannel.organization_id == model.organization_id,
                    models.AlertChannel.is_active == True  # noqa: E712
                )
                .all()
            )
            
            # Send notifications
            for channel in alert_channels:
                try:
                    # Run async functions in the event loop
                    loop = None
                    try:
                        loop = asyncio.get_running_loop()
                    except RuntimeError:
                        loop = None
                    
                    if str(channel.channel_type) == "email":
                        if loop:
                            asyncio.create_task(
                                notification_service.send_email_alert(
                                    channel, model, ks_statistic, p_value
                                )
                            )
                        else:
                            asyncio.run(
                                notification_service.send_email_alert(
                                    channel, model, ks_statistic, p_value
                                )
                            )
                    elif str(channel.channel_type) == "slack":
                        if loop:
                            asyncio.create_task(
                                notification_service.send_slack_alert(
                                    channel, model, ks_statistic, p_value
                                )
                            )
                        else:
                            asyncio.run(
                                notification_service.send_slack_alert(
                                    channel, model, ks_statistic, p_value
                                )
                            )
                except Exception as e:
                    print(f"Failed to send notification via {channel.channel_type}: {e}")

        # g. Always return a dictionary with the results
        return {
            "drift_detected": drift_detected,
            "drift_score": ks_statistic,
            "p_value": p_value,
            "samples": len(current_values),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
