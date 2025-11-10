"""
CRUD operations for Cognitude LLM Monitoring Platform.
"""
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, Integer
from decimal import Decimal
import hashlib
import json
from typing import Optional, List, Dict, Any

from . import models, schemas


# ============================================================================
# Organization CRUD (kept from original)
# ============================================================================

def get_organization_by_api_key_hash(db: Session, api_key_hash: str):
    """Get organization by API key hash."""
    return db.query(models.Organization).filter(
        models.Organization.api_key_hash == api_key_hash
    ).first()


def get_organizations(db: Session):
    """Get all organizations."""
    return db.query(models.Organization).all()


def create_organization(db: Session, organization: schemas.OrganizationCreate, api_key_hash: str):
    """Create a new organization."""
    db_organization = models.Organization(
        name=organization.name,
        api_key_hash=api_key_hash
    )
    db.add(db_organization)
    db.commit()
    db.refresh(db_organization)
    return db_organization


# ============================================================================
# LLM Request Logging
# ============================================================================

def log_llm_request(
    db: Session,
    organization_id: int,
    model: str,
    provider: str,
    prompt_tokens: int,
    completion_tokens: int,
    cost_usd: Decimal,
    latency_ms: int,
    cache_hit: bool = False,
    cache_key: Optional[str] = None,
    endpoint: str = "/v1/chat/completions",
    status_code: int = 200,
    error_message: Optional[str] = None
) -> models.LLMRequest:
    """Log an LLM API request."""
    db_request = models.LLMRequest(
        organization_id=organization_id,
        model=model,
        provider=provider,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=prompt_tokens + completion_tokens,
        cost_usd=cost_usd,
        latency_ms=latency_ms,
        cache_hit=cache_hit,
        cache_key=cache_key,
        endpoint=endpoint,
        status_code=status_code,
        error_message=error_message
    )
    db.add(db_request)
    db.commit()
    db.refresh(db_request)
    return db_request


def get_llm_requests(
    db: Session,
    organization_id: int,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    limit: int = 100
) -> List[models.LLMRequest]:
    """Get LLM requests for an organization."""
    query = db.query(models.LLMRequest).filter(
        models.LLMRequest.organization_id == organization_id
    )
    
    if start_date:
        query = query.filter(models.LLMRequest.timestamp >= start_date)
    if end_date:
        query = query.filter(models.LLMRequest.timestamp <= end_date)
    
    return query.order_by(models.LLMRequest.timestamp.desc()).limit(limit).all()


# ============================================================================
# Cache Operations
# ============================================================================

def generate_cache_key(messages: List[Dict], model: str, temperature: float = 1.0) -> str:
    """Generate cache key from request parameters."""
    cache_input = {
        "messages": messages,
        "model": model,
        "temperature": temperature
    }
    cache_string = json.dumps(cache_input, sort_keys=True)
    return hashlib.md5(cache_string.encode()).hexdigest()


def get_from_cache(db: Session, cache_key: str) -> Optional[models.LLMCache]:
    """Check if response exists in cache and is not expired."""
    cache_entry = db.query(models.LLMCache).filter(
        models.LLMCache.cache_key == cache_key
    ).first()
    
    if not cache_entry:
        return None
    
    # Check if expired
    expiry_time = cache_entry.created_at + timedelta(hours=cache_entry.ttl_hours)
    if datetime.utcnow() > expiry_time:
        # Cache expired, delete it
        db.delete(cache_entry)
        db.commit()
        return None
    
    # Update access stats
    cache_entry.last_accessed = datetime.utcnow()
    cache_entry.hit_count += 1
    db.commit()
    
    return cache_entry


def store_in_cache(
    db: Session,
    cache_key: str,
    prompt_hash: str,
    model: str,
    response_json: Dict[str, Any],
    ttl_hours: int = 24
) -> models.LLMCache:
    """Store response in cache."""
    cache_entry = models.LLMCache(
        cache_key=cache_key,
        prompt_hash=prompt_hash,
        model=model,
        response_json=response_json,
        ttl_hours=ttl_hours
    )
    db.add(cache_entry)
    db.commit()
    db.refresh(cache_entry)
    return cache_entry


def clear_cache(
    db: Session,
    model: Optional[str] = None,
    older_than_hours: Optional[int] = None
) -> int:
    """Clear cache entries based on filters."""
    query = db.query(models.LLMCache)
    
    if model:
        query = query.filter(models.LLMCache.model == model)
    
    if older_than_hours:
        cutoff_time = datetime.utcnow() - timedelta(hours=older_than_hours)
        query = query.filter(models.LLMCache.created_at < cutoff_time)
    
    count = query.count()
    query.delete()
    db.commit()
    
    return count


def get_cache_stats(db: Session) -> Dict[str, Any]:
    """Get cache statistics."""
    total_entries = db.query(func.count(models.LLMCache.cache_key)).scalar()
    total_hits = db.query(func.sum(models.LLMCache.hit_count)).scalar() or 0
    
    # Calculate hit rate from request logs
    total_requests = db.query(func.count(models.LLMRequest.id)).scalar()
    cached_requests = db.query(func.count(models.LLMRequest.id)).filter(
        models.LLMRequest.cache_hit == True
    ).scalar()
    
    hit_rate = cached_requests / total_requests if total_requests > 0 else 0.0
    
    # Estimate savings (rough calculation)
    # Assume average cached request saves $0.002
    estimated_savings = cached_requests * 0.002
    
    return {
        "total_entries": total_entries,
        "total_hits": total_hits,
        "hit_rate": hit_rate,
        "estimated_savings_usd": estimated_savings
    }


# ============================================================================
# Provider Configuration
# ============================================================================

def create_provider_config(
    db: Session,
    organization_id: int,
    provider: str,
    api_key_encrypted: str,
    enabled: bool = True,
    priority: int = 0
) -> models.ProviderConfig:
    """Create provider configuration."""
    config = models.ProviderConfig(
        organization_id=organization_id,
        provider=provider,
        api_key_encrypted=api_key_encrypted,
        enabled=enabled,
        priority=priority
    )
    db.add(config)
    db.commit()
    db.refresh(config)
    return config


def get_provider_configs(
    db: Session,
    organization_id: int,
    enabled_only: bool = False
) -> List[models.ProviderConfig]:
    """Get provider configurations for an organization."""
    query = db.query(models.ProviderConfig).filter(
        models.ProviderConfig.organization_id == organization_id
    )
    
    if enabled_only:
        query = query.filter(models.ProviderConfig.enabled == True)
    
    return query.order_by(models.ProviderConfig.priority.desc()).all()


def get_provider_config(db: Session, config_id: int) -> Optional[models.ProviderConfig]:
    """Get a specific provider configuration."""
    return db.query(models.ProviderConfig).filter(
        models.ProviderConfig.id == config_id
    ).first()


def update_provider_config(
    db: Session,
    config_id: int,
    updates: schemas.ProviderConfigUpdate
) -> Optional[models.ProviderConfig]:
    """Update provider configuration."""
    config = get_provider_config(db, config_id)
    if not config:
        return None
    
    if updates.enabled is not None:
        config.enabled = updates.enabled
    if updates.priority is not None:
        config.priority = updates.priority
    if updates.api_key is not None:
        # In production, encrypt this
        config.api_key_encrypted = updates.api_key
    
    db.commit()
    db.refresh(config)
    return config


def delete_provider_config(db: Session, config_id: int) -> bool:
    """Delete provider configuration."""
    config = get_provider_config(db, config_id)
    if not config:
        return False
    
    db.delete(config)
    db.commit()
    return True


# ============================================================================
# Analytics
# ============================================================================

def get_analytics(
    db: Session,
    organization_id: int,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
) -> Dict[str, Any]:
    """Get comprehensive analytics for an organization."""
    query = db.query(models.LLMRequest).filter(
        models.LLMRequest.organization_id == organization_id
    )
    
    if start_date:
        query = query.filter(models.LLMRequest.timestamp >= start_date)
    if end_date:
        query = query.filter(models.LLMRequest.timestamp <= end_date)
    
    # Total metrics
    total_requests = query.count()
    total_cost = db.query(func.sum(models.LLMRequest.cost_usd)).filter(
        models.LLMRequest.organization_id == organization_id
    ).scalar() or 0.0
    
    avg_latency = db.query(func.avg(models.LLMRequest.latency_ms)).filter(
        models.LLMRequest.organization_id == organization_id
    ).scalar() or 0.0
    
    total_tokens = db.query(func.sum(models.LLMRequest.total_tokens)).filter(
        models.LLMRequest.organization_id == organization_id
    ).scalar() or 0
    
    cached_requests = query.filter(models.LLMRequest.cache_hit == True).count()
    cache_hit_rate = cached_requests / total_requests if total_requests > 0 else 0.0
    
    # Daily breakdown
    daily_query = db.query(
        func.date(models.LLMRequest.timestamp).label('date'),
        func.count(models.LLMRequest.id).label('requests'),
        func.sum(models.LLMRequest.cost_usd).label('cost'),
        func.sum(func.cast(models.LLMRequest.cache_hit, Integer)).label('cached_requests')
    ).filter(
        models.LLMRequest.organization_id == organization_id
    )
    
    if start_date:
        daily_query = daily_query.filter(models.LLMRequest.timestamp >= start_date)
    if end_date:
        daily_query = daily_query.filter(models.LLMRequest.timestamp <= end_date)
    
    usage_by_day = daily_query.group_by(func.date(models.LLMRequest.timestamp)).all()
    
    # Provider breakdown
    provider_query = db.query(
        models.LLMRequest.provider,
        func.count(models.LLMRequest.id).label('requests'),
        func.sum(models.LLMRequest.cost_usd).label('cost'),
        func.avg(models.LLMRequest.latency_ms).label('avg_latency_ms')
    ).filter(
        models.LLMRequest.organization_id == organization_id
    )
    
    if start_date:
        provider_query = provider_query.filter(models.LLMRequest.timestamp >= start_date)
    if end_date:
        provider_query = provider_query.filter(models.LLMRequest.timestamp <= end_date)
    
    usage_by_provider = provider_query.group_by(models.LLMRequest.provider).all()
    
    # Model breakdown
    model_query = db.query(
        models.LLMRequest.model,
        func.count(models.LLMRequest.id).label('requests'),
        func.sum(models.LLMRequest.cost_usd).label('cost'),
        func.sum(models.LLMRequest.total_tokens).label('total_tokens')
    ).filter(
        models.LLMRequest.organization_id == organization_id
    )
    
    if start_date:
        model_query = model_query.filter(models.LLMRequest.timestamp >= start_date)
    if end_date:
        model_query = model_query.filter(models.LLMRequest.timestamp <= end_date)
    
    usage_by_model = model_query.group_by(models.LLMRequest.model).all()
    
    return {
        "total_requests": total_requests,
        "total_cost": float(total_cost),
        "average_latency": float(avg_latency),
        "cache_hit_rate": cache_hit_rate,
        "total_tokens": total_tokens,
        "usage_by_day": [
            {
                "date": str(row.date),
                "requests": row.requests,
                "cost": float(row.cost or 0),
                "cached_requests": row.cached_requests or 0,
                "cache_savings": 0.0  # Calculate based on average cost
            }
            for row in usage_by_day
        ],
        "usage_by_provider": [
            {
                "provider": row.provider,
                "requests": row.requests,
                "cost": float(row.cost or 0),
                "avg_latency_ms": float(row.avg_latency_ms or 0)
            }
            for row in usage_by_provider
        ],
        "usage_by_model": [
            {
                "model": row.model,
                "requests": row.requests,
                "cost": float(row.cost or 0),
                "total_tokens": row.total_tokens or 0
            }
            for row in usage_by_model
        ]
    }

