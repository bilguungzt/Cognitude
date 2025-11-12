"""
Monitoring endpoints for health checks and system status.
"""
from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session
from sqlalchemy import text
from prometheus_client import Counter, Histogram, generate_latest

from ..database import get_db
from ..services.redis_cache import redis_cache, redis

router = APIRouter()

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
    # 1. Check Database Connection
    try:
        db.execute(text("SELECT 1"))
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail={"status": "unhealthy", "service": "database", "error": str(e)},
        )

    # 2. Check Redis Connection
    if not redis_cache.available or not redis_cache.redis:
        raise HTTPException(
            status_code=503,
            detail={"status": "unhealthy", "service": "redis", "error": "Redis client not available"},
        )
    try:
        redis_cache.redis.ping()
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail={"status": "unhealthy", "service": "redis", "error": str(e)},
        )

    return {"status": "healthy"}