from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app import models, schemas
from app.database import get_db
from sqlalchemy import func, case
from datetime import datetime, timedelta
from app.security import get_organization_from_api_key

router = APIRouter(tags=["Dashboard"])

@router.get("/summary", response_model=schemas.DashboardSummaryStats)
def get_dashboard_summary_statistics(
    db: Session = Depends(get_db),
    organization: schemas.Organization = Depends(get_organization_from_api_key)
):
    """
    Get summary statistics for the dashboard.
    """
    try:
        # Calculate total cost savings (example logic - adjust as needed)
        total_cost_savings = db.query(func.sum(models.AutopilotLog.estimated_savings_usd)).scalar() or 0.0

        # Calculate autopilot decisions today
        today = datetime.utcnow().date()
        autopilot_decisions_today = db.query(models.AutopilotLog).filter(
            func.date(models.AutopilotLog.timestamp) == today
        ).count()

        # Calculate validation failures in the last 24 hours
        twenty_four_hours_ago = datetime.utcnow() - timedelta(hours=24)
        validation_failures_last_24h = db.query(models.ValidationLog).filter(
            models.ValidationLog.timestamp >= twenty_four_hours_ago,
            models.ValidationLog.was_successful == False
        ).count()

        # Count active schemas - count the number of schema validation attempts
        active_schemas = db.query(models.SchemaValidationLog).count()

        return {
          "total_cost_savings": float(total_cost_savings) if total_cost_savings is not None else 0.0,
          "autopilot_decisions_today": autopilot_decisions_today,
          "validation_failures_last_24h": validation_failures_last_24h,
          "active_schemas": active_schemas
        }
    except Exception as e:
        # Log the error for debugging
        print(f"Error in get_dashboard_summary_statistics: {str(e)}")
        # Return default values to prevent hanging
        return {
          "total_cost_savings": 0.0,
          "autopilot_decisions_today": 0,
          "validation_failures_last_24h": 0,
          "active_schemas": 0
        }

@router.get("/schema-stats", response_model=schemas.TopSchemaStatsResponse)
def get_schema_stats(
    db: Session = Depends(get_db),
    organization: schemas.Organization = Depends(get_organization_from_api_key)
):
    """
    Get statistics for the top 5 most used schemas based on attempt count.
    """
    try:
        top_rows = (
            db.query(
                models.SchemaValidationLog.schema_hash,
                func.count(models.SchemaValidationLog.id).label("total_attempts"),
                (
                    func.sum(case((models.SchemaValidationLog.was_successful == False, 1), else_=0))
                    * 1.0
                    / func.count(models.SchemaValidationLog.id)
                ).label("failure_rate"),
                func.avg(models.SchemaValidationLog.retry_count).label("avg_retries"),
            )
            .group_by(models.SchemaValidationLog.schema_hash)
            .order_by(func.count(models.SchemaValidationLog.id).desc())
            .limit(5)
            .all()
        )

        # Convert SQLAlchemy row results into the shape the frontend expects
        top_5_most_used = [
            {
                "schema_name": row.schema_hash,
                "total_attempts": int(row.total_attempts),
                "failure_rate": float(row.failure_rate or 0.0),
                "avg_retries": float(row.avg_retries or 0.0),
            }
            for row in top_rows
        ]

        return {"top_5_most_used": top_5_most_used}
    except Exception as e:
        # Log the error for debugging
        print(f"Error in get_schema_stats: {str(e)}")
        # Return empty result to prevent hanging
        return {"top_5_most_used": []}