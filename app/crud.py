"""
CRUD operations for Cognitude LLM Monitoring Platform.
Fixed version with proper SQLAlchemy type handling.
"""
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from sqlalchemy import func, Integer, cast, case
from decimal import Decimal
import hashlib
import json
from typing import Optional, List, Dict, Any

from . import models, schemas


# ============================================================================
# Organization CRUD
# ============================================================================

def get_organization_by_api_key_hash(db: Session, api_key_hash: str) -> Optional[models.Organization]:
    """Get organization by API key hash."""
    return db.query(models.Organization).filter(
        models.Organization.api_key_hash == api_key_hash
    ).first()


def get_organizations(db: Session) -> List[models.Organization]:
    """Get all organizations."""
    return db.query(models.Organization).all()


def create_organization(
    db: Session, 
    organization: schemas.OrganizationCreate, 
    api_key_hash: str
) -> models.Organization:
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

def generate_cache_key(messages: List[Dict[str, Any]], model: str, temperature: float = 1.0) -> str:
    """Generate cache key from request parameters."""
    cache_input = {
        "messages": messages,
        "model": model,
        "temperature": temperature
    }
    cache_string = json.dumps(cache_input, sort_keys=True)
    return hashlib.md5(cache_string.encode()).hexdigest()


def get_from_cache(db: Session, cache_key: str) -> Optional[models.LLMCache]:
    """
    Check if response exists in cache and is not expired.
    This is a READ-ONLY operation.
    """
    cache_entry = db.query(models.LLMCache).filter(
        models.LLMCache.cache_key == cache_key
    ).first()
    
    if not cache_entry:
        return None
    
    # Check if expired
    # Access the raw values from the SQLAlchemy object instance to avoid Column type errors
    # Use hasattr and getattr with a fallback to the object's attribute for robustness
    raw_created_at = getattr(cache_entry, 'created_at', None)
    raw_ttl_hours = getattr(cache_entry, 'ttl_hours', None)
    
    if raw_created_at is not None and raw_ttl_hours is not None:
        try:
            now = datetime.now(timezone.utc)
            if raw_created_at.tzinfo is None:
                raw_created_at = raw_created_at.replace(tzinfo=timezone.utc)
            
            expiry_time = raw_created_at + timedelta(hours=float(raw_ttl_hours))
            
            if now > expiry_time:
                # Expired, but don't delete here. Let a background job handle it.
                return None
        except (ValueError, TypeError, AttributeError):
            return None # Treat as expired if there's an error
            
    return cache_entry


def update_cache_stats(db: Session, cache_key: str):
    """
    Update cache statistics for a cache hit. This is a WRITE operation.
    """
    # Use a scalar subquery or a direct update with a value, not a Column reference for the increment
    db.query(models.LLMCache).filter(models.LLMCache.cache_key == cache_key).update(
        {
            models.LLMCache.hit_count: models.LLMCache.hit_count + 1,
            models.LLMCache.last_accessed: datetime.now(timezone.utc),
        },
        synchronize_session=False,
    )
    db.commit()


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
        ttl_hours=ttl_hours,
        hit_count=0
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
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=older_than_hours)
        query = query.filter(models.LLMCache.created_at < cutoff_time)
    
    count = query.count()
    query.delete(synchronize_session=False)
    db.commit()
    
    return count


def get_cache_stats(db: Session) -> Dict[str, Any]:
    """Get cache statistics."""
    total_entries = db.query(func.count(models.LLMCache.cache_key)).scalar() or 0
    total_hits = db.query(func.sum(models.LLMCache.hit_count)).scalar() or 0
    
    # Calculate hit rate from request logs
    total_requests = db.query(func.count(models.LLMRequest.id)).scalar() or 0
    cached_requests = db.query(func.count(models.LLMRequest.id)).filter(
        models.LLMRequest.cache_hit == True  # noqa: E712
    ).scalar() or 0
    
    hit_rate = cached_requests / total_requests if total_requests > 0 else 0.0
    
    # Calculate savings by summing the cost of all cached requests
    # Use == True for boolean comparison with SQLAlchemy, and suppress the linter warning
    savings_query = db.query(func.sum(models.LLMRequest.cost_usd)).filter(
        models.LLMRequest.cache_hit == True  # noqa: E712
    )
    estimated_savings = savings_query.scalar() or Decimal(0)
    
    return {
        "total_entries": int(total_entries),
        "total_hits": int(total_hits),
        "hit_rate": float(hit_rate),
        "estimated_savings_usd": float(estimated_savings)
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
        query = query.filter(models.ProviderConfig.enabled == True)  # noqa: E712
    
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
    
    update_data = updates.model_dump(exclude_unset=True)
    
    # Properly update attributes
    if "api_key" in update_data:
        config.api_key_encrypted = update_data["api_key"]
    if "enabled" in update_data:
        config.enabled = update_data["enabled"]
    if "priority" in update_data:
        config.priority = update_data["priority"]
    
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
    
    # Total metrics with proper null handling
    total_requests = query.count()
    
    cost_query = db.query(func.sum(models.LLMRequest.cost_usd)).filter(
        models.LLMRequest.organization_id == organization_id
    )
    if start_date:
        cost_query = cost_query.filter(models.LLMRequest.timestamp >= start_date)
    if end_date:
        cost_query = cost_query.filter(models.LLMRequest.timestamp <= end_date)
    total_cost = cost_query.scalar() or Decimal(0)
    
    latency_query = db.query(func.avg(models.LLMRequest.latency_ms)).filter(
        models.LLMRequest.organization_id == organization_id
    )
    if start_date:
        latency_query = latency_query.filter(models.LLMRequest.timestamp >= start_date)
    if end_date:
        latency_query = latency_query.filter(models.LLMRequest.timestamp <= end_date)
    avg_latency = latency_query.scalar() or 0.0
    
    tokens_query = db.query(func.sum(models.LLMRequest.total_tokens)).filter(
        models.LLMRequest.organization_id == organization_id
    )
    if start_date:
        tokens_query = tokens_query.filter(models.LLMRequest.timestamp >= start_date)
    if end_date:
        tokens_query = tokens_query.filter(models.LLMRequest.timestamp <= end_date)
    total_tokens = tokens_query.scalar() or 0
    
    cached_requests = query.filter(models.LLMRequest.cache_hit == True).count()  # noqa: E712
    cache_hit_rate = cached_requests / total_requests if total_requests > 0 else 0.0
    
    # Daily breakdown
    daily_query = db.query(
        func.date(models.LLMRequest.timestamp).label('date'),
        func.count(models.LLMRequest.id).label('requests'),
        func.sum(models.LLMRequest.cost_usd).label('cost'),
        func.sum(cast(models.LLMRequest.cache_hit, Integer)).label('cached_requests')
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
        "total_requests": int(total_requests),
        "total_cost": float(total_cost),
        "average_latency": float(avg_latency),
        "cache_hit_rate": float(cache_hit_rate),
        "total_tokens": int(total_tokens),
        "usage_by_day": [
            {
                "date": str(row.date),
                "requests": int(row.requests),
                "cost": float(row.cost or 0),
                "cached_requests": int(row.cached_requests or 0),
                "cache_savings": 0.0
            }
            for row in usage_by_day
        ],
        "usage_by_provider": [
            {
                "provider": str(row.provider),
                "requests": int(row.requests),
                "cost": float(row.cost or 0),
                "avg_latency_ms": float(row.avg_latency_ms or 0)
            }
            for row in usage_by_provider
        ],
        "usage_by_model": [
            {
                "model": str(row.model),
                "requests": int(row.requests),
                "cost": float(row.cost or 0),
                "total_tokens": int(row.total_tokens or 0)
            }
            for row in usage_by_model
        ]
    }


# ============================================================================
# Schema Validation Logging
# ============================================================================

def create_schema_validation_log(
    db: Session, 
    log: schemas.SchemaValidationLogCreate
) -> models.SchemaValidationLog:
    """Create a new schema validation log entry."""
    db_log = models.SchemaValidationLog(**log.model_dump())
    db.add(db_log)
    db.commit()
    db.refresh(db_log)
    return db_log


def create_schema(db: Session, name: str, schema_data: Dict[str, Any], organization_id: int) -> models.Schema:
    """Create a new schema."""
    db_schema = models.Schema(
        name=name,
        schema_data=schema_data,
        organization_id=organization_id,
        is_active=True
    )
    db.add(db_schema)
    db.commit()
    db.refresh(db_schema)
    return db_schema


def get_schema_stats(db: Session, organization_id: int) -> List[Dict[str, Any]]:
    """
    Get schema statistics including usage and failure rates for all active schemas.
    Simplified version to avoid complex SQL queries.
    """
    from sqlalchemy import func

    # Get all active schemas for the organization
    active_schemas = db.query(models.Schema).filter(
        models.Schema.organization_id == organization_id,
        models.Schema.is_active == True
    ).all()

    if not active_schemas:
        return []

    results = []
    for schema in active_schemas:
        # Step 2: Get stats for each schema individually
        stats = db.query(
            func.count(models.SchemaValidationLog.id).label("total_attempts"),
            func.sum(case((models.SchemaValidationLog.is_valid == False, 1), else_=0)).label("failure_count"),
            func.avg(models.SchemaValidationLog.retry_count).label("avg_retries")
        ).filter(
            models.SchemaValidationLog.organization_id == organization_id,
            models.SchemaValidationLog.schema_id == schema.id
        ).first()

        total_attempts = stats.total_attempts if stats and stats.total_attempts is not None else 0
        failure_count = stats.failure_count if stats and stats.failure_count is not None else 0
        failure_rate = failure_count / total_attempts if total_attempts > 0 else 0.0
        avg_retries = stats.avg_retries if stats and stats.avg_retries is not None else 0.0

        results.append({
            "schema_name": schema.name,
            "total_attempts": total_attempts,
            "failure_rate": failure_rate,
            "avg_retries": avg_retries
        })
        
    return results


def get_failed_validation_logs(db: Session, organization_id: int) -> List[models.SchemaValidationLog]:
    """Get failed validation logs."""
    return db.query(models.SchemaValidationLog).filter(
        models.SchemaValidationLog.organization_id == organization_id,
        models.SchemaValidationLog.is_valid == False
    ).all()


# ============================================================================
# Provider Config CRUD
# ============================================================================

def create_provider_config(
    db: Session,
    organization_id: int,
    provider: str,
    api_key: str,
    enabled: bool = True,
    priority: int = 1
) -> models.ProviderConfig:
    """Create a new provider configuration."""
    db_provider = models.ProviderConfig(
        organization_id=organization_id,
        provider=provider,
        api_key_encrypted=api_key,  # Note: should be encrypted in production
        enabled=enabled,
        priority=priority
    )
    db.add(db_provider)
    db.commit()
    db.refresh(db_provider)
    return db_provider


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
    return query.all()


def update_provider_config(
    db: Session,
    config_id: int,
    updates: Dict[str, Any]
) -> Optional[models.ProviderConfig]:
    """Update a provider configuration."""
    provider = db.query(models.ProviderConfig).filter(
        models.ProviderConfig.id == config_id
    ).first()
    
    if not provider:
        return None
    
    for key, value in updates.items():
        if hasattr(provider, key):
            setattr(provider, key, value)
    
    db.commit()
    db.refresh(provider)
    return provider


def delete_provider_config(db: Session, config_id: int) -> bool:
    """Delete a provider configuration."""
    provider = db.query(models.ProviderConfig).filter(
        models.ProviderConfig.id == config_id
    ).first()
    
    if not provider:
        return False
    
    db.delete(provider)
    db.commit()
    return True