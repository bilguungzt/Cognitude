"""
Background scheduler for running drift detection automatically
"""
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime
import logging

from sqlalchemy.orm import Session
from . import models
from .database import SessionLocal
from .services.drift_detection import DriftDetectionService

logger = logging.getLogger(__name__)


class DriftDetectionScheduler:
    """Scheduler for automatic drift detection"""
    
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.is_running = False
        
    def check_all_models_for_drift(self):
        """
        Run drift detection for all registered models
        This function is called periodically by the scheduler
        """
        db: Session = SessionLocal()
        
        try:
            # Get all models
            models_list = db.query(models.Model).all()
            
            logger.info(f"Running scheduled drift check for {len(models_list)} models")
            
            for model in models_list:
                try:
                    # Run drift detection for this model
                    drift_service = DriftDetectionService(db)
                    model_id = int(model.id)  # type: ignore
                    result = drift_service.calculate_ks_test_drift(model_id=model_id)
                    
                    if result:
                        status = "DRIFT DETECTED" if result.get('drift_detected') else "OK"
                        logger.info(
                            f"Model {model.id} ({model.name}): {status} "
                            f"[score: {result.get('drift_score', 0):.3f}, "
                            f"p-value: {result.get('p_value', 1):.4f}]"
                        )
                    else:
                        logger.debug(f"Model {model.id} ({model.name}): Insufficient data for drift check")
                        
                except Exception as e:
                    logger.error(f"Error checking drift for model {model.id}: {str(e)}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error in scheduled drift check: {str(e)}")
        finally:
            db.close()
    
    def start(self, interval_minutes: int = 15):
        """
        Start the background scheduler
        
        Args:
            interval_minutes: How often to run drift detection (default: 15 minutes)
        """
        if self.is_running:
            logger.warning("Scheduler is already running")
            return
        
        # Add the job to run periodically
        self.scheduler.add_job(
            func=self.check_all_models_for_drift,
            trigger=IntervalTrigger(minutes=interval_minutes),
            id='drift_detection_job',
            name='Drift Detection Check',
            replace_existing=True
        )
        
        # Start the scheduler
        self.scheduler.start()
        self.is_running = True
        
        logger.info(f"✅ Drift detection scheduler started (runs every {interval_minutes} minutes)")
        logger.info(f"   Next run scheduled for: {datetime.now()}")
        
    def stop(self):
        """Stop the background scheduler"""
        if self.is_running:
            self.scheduler.shutdown()
            self.is_running = False
            logger.info("Drift detection scheduler stopped")
    
    def run_now(self):
        """Manually trigger a drift check immediately"""
        logger.info("Manual drift check triggered")
        self.check_all_models_for_drift()
    
    def get_status(self):
        """Get scheduler status information"""
        jobs = self.scheduler.get_jobs()
        
        return {
            "is_running": self.is_running,
            "jobs": [
                {
                    "id": job.id,
                    "name": job.name,
                    "next_run": job.next_run_time.isoformat() if job.next_run_time else None
                }
                for job in jobs
            ]
        }


# Global scheduler instance
scheduler = DriftDetectionScheduler()
