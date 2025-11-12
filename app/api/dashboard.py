from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app import models, schemas
from app.database import get_db
from sqlalchemy import func, case

router = APIRouter()

@router.get("/schema-stats", response_model=schemas.TopSchemaStatsResponse)
def get_schema_stats(db: Session = Depends(get_db)):
    """
    Get statistics for the top 5 most used schemas based on attempt count.
    """
    top_schemas = (
        db.query(
            models.SchemaValidationLog.schema_hash,
            func.count(models.SchemaValidationLog.id).label("total_attempts"),
            (
                func.sum(case((models.SchemaValidationLog.was_successful == False, 1), else_=0))
                * 100.0
                / func.count(models.SchemaValidationLog.id)
            ).label("failure_rate"),
            func.avg(models.SchemaValidationLog.retry_count).label("avg_retries"),
        )
        .group_by(models.SchemaValidationLog.schema_hash)
        .order_by(func.count(models.SchemaValidationLog.id).desc())
        .limit(5)
        .all()
    )

    return {"top_schemas": top_schemas}