"""
Business metrics dashboard API for comprehensive monitoring and analytics.
"""
from datetime import datetime, timedelta
from typing import Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app import models
from app.security import get_organization_from_api_key
from app.services.tracing import tracer

router = APIRouter(tags=["metrics"])


@router.get("/summary", response_model=Dict[str, Any])
async def get_metrics_summary(
    db: Session = Depends(get_db),
    organization: models.Organization = Depends(get_organization_from_api_key)
):
    """
    Get comprehensive business metrics summary for dashboard.
    """
    with tracer.start_as_current_span("get_metrics_summary") as span:
        org_id = organization.id
        span.set_attribute("organization.id", org_id)
        
        # Time ranges
        now = datetime.utcnow()
        last_24h = now - timedelta(hours=24)
        last_7d = now - timedelta(days=7)
        last_30d = now - timedelta(days=30)
        
        metrics = {}
        
        # Request volume metrics
        with tracer.start_as_current_span("calculate_request_metrics"):
            total_requests = db.query(models.LLMRequest).filter(
                models.LLMRequest.organization_id == org_id
            ).count()
            
            requests_24h = db.query(models.LLMRequest).filter(
                models.LLMRequest.organization_id == org_id,
                models.LLMRequest.timestamp >= last_24h
            ).count()
            
            requests_7d = db.query(models.LLMRequest).filter(
                models.LLMRequest.organization_id == org_id,
                models.LLMRequest.timestamp >= last_7d
            ).count()
            
            requests_30d = db.query(models.LLMRequest).filter(
                models.LLMRequest.organization_id == org_id,
                models.LLMRequest.timestamp >= last_30d
            ).count()
            
            metrics["requests"] = {
                "total": total_requests,
                "last_24h": requests_24h,
                "last_7d": requests_7d,
                "last_30d": requests_30d
            }
        
        # Cost metrics
        with tracer.start_as_current_span("calculate_cost_metrics"):
            from sqlalchemy import func
            
            total_cost = db.query(func.sum(models.LLMRequest.cost_usd)).filter(
                models.LLMRequest.organization_id == org_id
            ).scalar() or 0
            
            cost_24h = db.query(func.sum(models.LLMRequest.cost_usd)).filter(
                models.LLMRequest.organization_id == org_id,
                models.LLMRequest.timestamp >= last_24h
            ).scalar() or 0
            
            cost_7d = db.query(func.sum(models.LLMRequest.cost_usd)).filter(
                models.LLMRequest.organization_id == org_id,
                models.LLMRequest.timestamp >= last_7d
            ).scalar() or 0
            
            cost_30d = db.query(func.sum(models.LLMRequest.cost_usd)).filter(
                models.LLMRequest.organization_id == org_id,
                models.LLMRequest.timestamp >= last_30d
            ).scalar() or 0
            
            metrics["cost"] = {
                "total_usd": float(total_cost),
                "last_24h_usd": float(cost_24h),
                "last_7d_usd": float(cost_7d),
                "last_30d_usd": float(cost_30d)
            }
        
        # Cache performance metrics
        with tracer.start_as_current_span("calculate_cache_metrics"):
            cached_requests = db.query(models.LLMRequest).filter(
                models.LLMRequest.organization_id == org_id,
                models.LLMRequest.cache_hit == True
            ).count()
            
            cached_24h = db.query(models.LLMRequest).filter(
                models.LLMRequest.organization_id == org_id,
                models.LLMRequest.cache_hit == True,
                models.LLMRequest.timestamp >= last_24h
            ).count()
            
            cache_hit_rate = (cached_requests / total_requests * 100) if total_requests > 0 else 0
            cache_hit_rate_24h = (cached_24h / requests_24h * 100) if requests_24h > 0 else 0
            
            # Calculate cache savings
            cache_savings = db.query(func.sum(models.LLMRequest.cost_usd)).filter(
                models.LLMRequest.organization_id == org_id,
                models.LLMRequest.cache_hit == True
            ).scalar() or 0
            
            metrics["cache"] = {
                "total_cached": cached_requests,
                "hit_rate_percent": round(cache_hit_rate, 2),
                "hit_rate_24h_percent": round(cache_hit_rate_24h, 2),
                "estimated_savings_usd": float(cache_savings)
            }
        
        # Performance metrics
        with tracer.start_as_current_span("calculate_performance_metrics"):
            avg_latency = db.query(func.avg(models.LLMRequest.latency_ms)).filter(
                models.LLMRequest.organization_id == org_id
            ).scalar() or 0
            
            avg_latency_24h = db.query(func.avg(models.LLMRequest.latency_ms)).filter(
                models.LLMRequest.organization_id == org_id,
                models.LLMRequest.timestamp >= last_24h
            ).scalar() or 0
            
            # Token usage
            total_tokens = db.query(func.sum(models.LLMRequest.total_tokens)).filter(
                models.LLMRequest.organization_id == org_id
            ).scalar() or 0
            
            prompt_tokens = db.query(func.sum(models.LLMRequest.prompt_tokens)).filter(
                models.LLMRequest.organization_id == org_id
            ).scalar() or 0
            
            completion_tokens = db.query(func.sum(models.LLMRequest.completion_tokens)).filter(
                models.LLMRequest.organization_id == org_id
            ).scalar() or 0
            
            metrics["performance"] = {
                "avg_latency_ms": round(avg_latency, 2),
                "avg_latency_24h_ms": round(avg_latency_24h, 2),
                "total_tokens": int(total_tokens),
                "prompt_tokens": int(prompt_tokens),
                "completion_tokens": int(completion_tokens)
            }
        
        # Provider usage breakdown
        with tracer.start_as_current_span("calculate_provider_metrics"):
            provider_usage = db.query(
                models.LLMRequest.provider,
                func.count(models.LLMRequest.id).label('count'),
                func.sum(models.LLMRequest.cost_usd).label('cost')
            ).filter(
                models.LLMRequest.organization_id == org_id
            ).group_by(models.LLMRequest.provider).all()
            
            metrics["providers"] = [
                {
                    "provider": str(p.provider),
                    "requests": int(p.count),
                    "cost_usd": float(p.cost or 0)
                }
                for p in provider_usage
            ]
        
        # Model usage breakdown
        with tracer.start_as_current_span("calculate_model_metrics"):
            model_usage = db.query(
                models.LLMRequest.model,
                func.count(models.LLMRequest.id).label('count'),
                func.sum(models.LLMRequest.cost_usd).label('cost')
            ).filter(
                models.LLMRequest.organization_id == org_id
            ).group_by(models.LLMRequest.model).all()
            
            metrics["models"] = [
                {
                    "model": str(m.model),
                    "requests": int(m.count),
                    "cost_usd": float(m.cost or 0)
                }
                for m in model_usage
            ]
        
        # Error rates
        with tracer.start_as_current_span("calculate_error_metrics"):
            total_errors = db.query(models.LLMRequest).filter(
                models.LLMRequest.organization_id == org_id,
                models.LLMRequest.status_code >= 400
            ).count()
            
            errors_24h = db.query(models.LLMRequest).filter(
                models.LLMRequest.organization_id == org_id,
                models.LLMRequest.status_code >= 400,
                models.LLMRequest.timestamp >= last_24h
            ).count()
            
            error_rate = (total_errors / total_requests * 100) if total_requests > 0 else 0
            error_rate_24h = (errors_24h / requests_24h * 100) if requests_24h > 0 else 0
            
            metrics["errors"] = {
                "total_errors": total_errors,
                "error_rate_percent": round(error_rate, 2),
                "error_rate_24h_percent": round(error_rate_24h, 2)
            }
        
        span.set_attribute("metrics.calculated", True)
        
        return {
            "timestamp": now.isoformat(),
            "organization_id": org_id,
            "metrics": metrics
        }