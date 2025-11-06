from apscheduler.schedulers.asyncio import AsyncIOScheduler
import logging

from ..database import SessionLocal
from ..services.drift_detection import DriftDetectionService
from .. import models as db_models

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()

def check_all_models_for_drift():
    """
    Scheduled job to check all models for data drift.
    Runs every 15 minutes and checks each model that has baseline configured.
    """
    db = None
    try:
        db = SessionLocal()
        drift_service = DriftDetectionService(db)
        
        # Get all models
        models_list = db.query(db_models.Model).all()
        
        logger.info(f"🔍 Running scheduled drift check for {len(models_list)} model(s)")
        
        checked_count = 0
        drift_detected_count = 0
        
        for model in models_list:
            try:
                model_id = int(model.id)  # type: ignore
                model_name = str(model.name)  # type: ignore
                
                # Check if model has baseline configured
                features = db.query(db_models.ModelFeature).filter(
                    db_models.ModelFeature.model_id == model_id
                ).all()
                
                has_baseline = any(f.baseline_stats for f in features)
                
                if not has_baseline:
                    logger.debug(f"⏭️  Skipping model {model_id} ({model_name}) - no baseline configured")
                    continue
                
                # Run drift detection
                result = drift_service.calculate_ks_test_drift(model_id=model_id)
                
                if result:
                    checked_count += 1
                    
                    if result.get('drift_detected'):
                        drift_detected_count += 1
                        logger.warning(
                            f"⚠️  DRIFT DETECTED - Model {model_id} ({model_name}): "
                            f"score={result.get('drift_score', 0):.3f}, "
                            f"p-value={result.get('p_value', 1):.4f}, "
                            f"samples={result.get('samples', 0)}"
                        )
                    else:
                        logger.info(
                            f"✅ OK - Model {model_id} ({model_name}): "
                            f"score={result.get('drift_score', 0):.3f}, "
                            f"p-value={result.get('p_value', 1):.4f}, "
                            f"samples={result.get('samples', 0)}"
                        )
                else:
                    logger.debug(
                        f"⏭️  Skipping model {model_id} ({model_name}) - "
                        f"insufficient data (<30 predictions in last 7 days)"
                    )
                    
            except Exception as e:
                logger.error(f"❌ Error checking drift for model {model.id}: {str(e)}")
                continue
        
        logger.info(
            f"✅ Drift check complete: {checked_count} models checked, "
            f"{drift_detected_count} drift(s) detected"
        )
                
    except Exception as e:
        logger.error(f"❌ Error in scheduled drift check: {str(e)}")
    finally:
        if db:
            db.close()

# Schedule the job to run every 15 minutes
scheduler.add_job(
    check_all_models_for_drift, 
    "interval", 
    minutes=15,
    id="drift_check_job",
    name="Drift Detection Check"
)

logger.info("📅 Drift detection scheduler configured (runs every 15 minutes)")
