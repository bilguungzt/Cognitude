import asyncio
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import func, text
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import LLMRequest
from app.services.redis_cache import redis_cache

router = APIRouter()

class BenchmarkMetrics(BaseModel):
    avg_cost: float = Field(..., description="Average cost of requests.")
    p50_latency: float = Field(..., description="50th percentile (median) latency in seconds.")
    p95_latency: float = Field(..., description="95th percentile latency in seconds.")
    success_rate: float = Field(..., description="Percentage of successful requests.")
    total_requests: int = Field(..., description="Total number of requests in the last 24 hours.")

class ModelBenchmark(BaseModel):
    model_name: str = Field(..., description="The name of the LLM.")
    metrics: BenchmarkMetrics = Field(..., description="Performance metrics for the model.")

class ProviderBenchmark(BaseModel):
    provider_name: str = Field(..., description="The name of the provider.")
    models: List[ModelBenchmark] = Field(..., description="List of model benchmarks for the provider.")

class PublicBenchmarksResponse(BaseModel):
    last_updated: datetime = Field(..., description="The timestamp when the benchmarks were last generated.")
    benchmarks: List[ProviderBenchmark] = Field(..., description="A list of benchmarks grouped by provider.")

def generate_benchmarks(db: Session):
    """
    Generates and caches LLM performance benchmarks.
    """
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(days=1)

    query = (
        text(f"""
            SELECT
                provider,
                model,
                AVG(cost_usd) as avg_cost,
                PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY latency_ms) as p50_latency,
                PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY latency_ms) as p95_latency,
                CAST(SUM(CASE WHEN status_code = 200 THEN 1 ELSE 0 END) AS FLOAT) / COUNT(*) as success_rate,
                COUNT(*) as total_requests
            FROM llm_requests
            WHERE timestamp BETWEEN '{start_time.isoformat()}' AND '{end_time.isoformat()}'
            GROUP BY provider, model
        """)
    )
    
    result = db.execute(query)
    rows = result.fetchall()

    provider_benchmarks: Dict[str, ProviderBenchmark] = {}

    for row in rows:
        provider_name, model_name, avg_cost, p50_latency, p95_latency, success_rate, total_requests = row
        
        if provider_name not in provider_benchmarks:
            provider_benchmarks[provider_name] = ProviderBenchmark(provider_name=provider_name, models=[])

        model_benchmark = ModelBenchmark(
            model_name=model_name,
            metrics=BenchmarkMetrics(
                avg_cost=avg_cost or 0.0,
                p50_latency=(p50_latency / 1000) if p50_latency is not None else 0.0,
                p95_latency=(p95_latency / 1000) if p95_latency is not None else 0.0,
                success_rate=(success_rate or 0.0) * 100,
                total_requests=total_requests or 0
            )
        )
        provider_benchmarks[provider_name].models.append(model_benchmark)

    response_data = PublicBenchmarksResponse(
        last_updated=end_time,
        benchmarks=list(provider_benchmarks.values())
    )
    
    if redis_cache.available:
        if redis_cache.redis:
            redis_cache.redis.set("public_benchmarks", response_data.model_dump_json(), ex=900) # 15 minutes expiration

@router.get("/v1/public/benchmarks/realtime", response_model=PublicBenchmarksResponse, status_code=status.HTTP_200_OK, summary="Get Real-time Public LLM Benchmarks")
def get_public_benchmarks(db: Session = Depends(get_db)):
    """
    Retrieves real-time LLM performance benchmarks from the cache.
    This endpoint is public and does not require authentication.
    """
    cached_benchmarks = None
    if redis_cache.available:
        if redis_cache.redis:
            cached_benchmarks = redis_cache.redis.get("public_benchmarks")
    if not cached_benchmarks:
        # In a real-world scenario, you might trigger an immediate regeneration
        # or return a specific status code indicating data is not yet available.
        # For now, we'll raise an error if the cache is empty.
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Benchmark data not available. Please try again in a few minutes."
        )
    
    return json.loads(cached_benchmarks)
