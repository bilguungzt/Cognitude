"""
Background scheduler for running drift detection automatically
"""
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime, timedelta
import logging

from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.api.public_benchmarks import generate_benchmarks
from app.services.reconciliation_service import ReconciliationService
from app.models import Organization

logger = logging.getLogger(__name__)


class CognitudeScheduler:
    """Scheduler for background jobs"""
    
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.is_running = False
        
    def run_benchmark_generation(self):
        """Generates and caches the public benchmarks."""
        db: Session = SessionLocal()
        try:
            logger.info("Running scheduled public benchmark generation.")
            generate_benchmarks(db)
            logger.info("Successfully generated and cached public benchmarks.")
        except Exception as e:
            logger.error(f"Error in scheduled benchmark generation: {str(e)}")
        finally:
            db.close()

    def run_daily_reconciliation(self):
        """Runs the billing reconciliation for all organizations."""
        db: Session = SessionLocal()
        try:
            logger.info("Starting daily billing reconciliation job.")
            reconciliation_service = ReconciliationService(db)
            organizations = db.query(Organization).all()
            
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=1)

            for org in organizations:
                # In a real-world scenario, the path to the external billing data
                # would be retrieved from a secure source. For this example, we'll
                # assume a placeholder path.
                external_source_path = f"/path/to/billing/data/{org.id}.csv"
                
                try:
                    reconciliation_service.run_reconciliation(
                        organization_id=getattr(org, 'id'),
                        start_date=start_date,
                        end_date=end_date,
                        external_source_path=external_source_path,
                    )
                    logger.info(f"Reconciliation completed for organization {org.id}.")
                except FileNotFoundError:
                    logger.warning(f"Billing data not found for organization {org.id} at {external_source_path}.")
                except Exception as e:
                    logger.error(f"Error during reconciliation for organization {org.id}: {str(e)}")

            logger.info("Daily billing reconciliation job finished.")
        except Exception as e:
            logger.error(f"Error in daily reconciliation job: {str(e)}")
        finally:
            db.close()

    def start(self):
        """Start the background scheduler"""
        if self.is_running:
            logger.warning("Scheduler is already running")
            return
        
        # Add the public benchmarks job
        self.scheduler.add_job(
            func=self.run_benchmark_generation,
            trigger=IntervalTrigger(minutes=15),
            id='public_benchmarks_job',
            name='Public Benchmarks Generation',
            replace_existing=True
        )
        
        # Add the daily reconciliation job
        self.scheduler.add_job(
            func=self.run_daily_reconciliation,
            trigger=IntervalTrigger(days=1),
            id='daily_reconciliation_job',
            name='Daily Billing Reconciliation',
            replace_existing=True,
        )
        
        # Start the scheduler
        self.scheduler.start()
        self.is_running = True
        
        logger.info(f"✅ Cognitude scheduler started.")
        
    def stop(self):
        """Stop the background scheduler"""
        if self.is_running:
            self.scheduler.shutdown()
            self.is_running = False
            logger.info("Benchmark scheduler stopped")
    
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
scheduler = CognitudeScheduler()
