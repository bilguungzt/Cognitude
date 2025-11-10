from apscheduler.schedulers.asyncio import AsyncIOScheduler
import logging

from ..database import SessionLocal
from ..services.alert_service import NotificationService
from .. import models as db_models

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()

# Note: Drift detection functionality has been removed
# This file now only handles alert checks

def check_alerts():
    """
    Scheduled job to check alert thresholds.
    Runs every hour and sends notifications for triggered alerts.
    """
    db = None
    try:
        db = SessionLocal()
        notification_service = NotificationService(db)
        
        # Check all active alert configurations
        notification_service.check_all_alerts()
        
        logger.info("✅ Alert check complete")
        
    except Exception as e:
        logger.error(f"❌ Error in scheduled alert check: {str(e)}")
    finally:
        if db:
            db.close()

# Schedule alert checks every hour
scheduler.add_job(
    check_alerts, 
    'interval',
    hours=1,
    id="alert_check_job",
    name="Alert Check",
    replace_existing=True
)

logger.info("📅 Alert scheduler configured (runs every hour)")
