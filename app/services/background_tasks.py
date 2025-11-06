from apscheduler.schedulers.asyncio import AsyncIOScheduler

from ..database import SessionLocal
from ..services.drift_detection import DriftDetectionService
from .. import crud

scheduler = AsyncIOScheduler()

def check_all_models_for_drift():
    """Scheduled job to check all models for data drift."""
    print("Running scheduled drift check for all models...")
    db = None
    try:
        db = SessionLocal()
        drift_service = DriftDetectionService(db)
        models = crud.get_all_models(db)
        for model in models:
            if model.baseline_mean is not None and model.baseline_std is not None:
                print(f"Checking model {model.id} ({model.name}) for drift...")
                result = drift_service.calculate_ks_test_drift(model.id)
                if result and result.get("drift_detected"):
                    print(f"Drift detected for model {model.id} ({model.name})!")
    except Exception as e:
        print(f"An error occurred during the drift check: {e}")
    finally:
        if db:
            db.close()

# Schedule the job to run every 15 minutes
scheduler.add_job(check_all_models_for_drift, "interval", minutes=15)
