"""
Background scheduler for running drift detection automatically
"""
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime
import logging

from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.api.public_benchmarks import generate_benchmarks

logger = logging.getLogger(__name__)


class BenchmarkScheduler:
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
        
        # Start the scheduler
        self.scheduler.start()
        self.is_running = True
        
        logger.info(f"✅ Benchmark scheduler started (runs every 15 minutes)")
        
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
scheduler = BenchmarkScheduler()
