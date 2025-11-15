"""
Monitoring endpoints for health checks and system status.
"""
from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session
from sqlalchemy import text
from prometheus_client import Counter, Histogram, generate_latest

from ..database import get_db
from ..services.redis_cache import redis_cache

router = APIRouter(tags=["Monitoring"])

# 1. Define Prometheus Metrics
request_count = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'status'])
request_latency = Histogram('http_request_duration_seconds', 'HTTP request latency', ['method', 'endpoint'])
autopilot_savings = Counter('autopilot_savings_usd_total', 'Total savings from autopilot', ['organization_id'])


@router.get("/metrics", tags=["monitoring"])
def get_metrics():
    """
    Prometheus metrics endpoint.
    """
    return Response(content=generate_latest(), media_type="text/plain")


@router.get("/health", tags=["monitoring"])
def health_check(db: Session = Depends(get_db)):
    """
    Health check endpoint for monitoring and load balancers.

    Checks the status of the database and Redis connections.
    """
    status_overall = "healthy"
    details = {"status": "healthy", "checks": {}}
    
    # 1. Check Database Connection
    try:
        db.execute(text("SELECT 1"))
        details["checks"]["database"] = {"status": "healthy"}
    except Exception as e:
        details["checks"]["database"] = {"status": "unhealthy", "error": str(e)}
        status_overall = "unhealthy"

    # 2. Check Redis Connection
    # NOTE: Redis is optional for basic functionality - the app can work without it
    # We'll log Redis status but won't fail the health check if Redis is unavailable
    if not redis_cache.available or not redis_cache.redis:
        details["checks"]["redis"] = {"status": "unavailable", "message": "Redis not available - using database fallback"}
    else:
        try:
            redis_cache.redis.ping()
            details["checks"]["redis"] = {"status": "healthy"}
        except Exception as e:
            details["checks"]["redis"] = {"status": "unhealthy", "error": str(e)}

    # Only fail health check if database is unhealthy (database is critical)
    if details["checks"]["database"]["status"] == "unhealthy":
        raise HTTPException(
            status_code=503,
            detail=details,
        )

    return details