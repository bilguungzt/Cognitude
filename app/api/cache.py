"""
Cache management API endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import crud, schemas
from ..database import get_db
from ..security import get_organization_from_api_key
from ..services.redis_cache import redis_cache
from ..services.cache_service import cache_service


router = APIRouter(prefix="/cache", tags=["Cache"])


@router.get("/stats", response_model=schemas.CacheStats)
def get_cache_statistics(
    db: Session = Depends(get_db),
    organization: schemas.Organization = Depends(get_organization_from_api_key)
):
    """
    Get cache statistics for the organization.
    
    Returns:
    - total_entries: Total cached responses
    - total_hits: Number of cache hits
    - hit_rate: Cache hit rate (0-1)
    - total_size_bytes: Approximate size of cached data
    - redis_status: Redis availability and stats
    """
    # Get Redis stats
    redis_stats = redis_cache.get_stats(organization.id)
    
    # Get PostgreSQL stats (for the entire database, as the function is not org-specific)
    pg_stats = crud.get_cache_stats(db)

    # If no stats are found, initialize with a zero state
    if not pg_stats:
        pg_stats = {
            "total_entries": 0,
            "total_hits": 0,
            "hit_rate": 0.0,
            "estimated_savings_usd": 0.0,
        }

    return {
        **pg_stats,
        "redis_available": redis_stats.get("redis_available", False),
        "redis_entries": redis_stats.get("total_entries", 0),
        "redis_hits": redis_stats.get("total_hits", 0),
    }


@router.post("/clear")
def clear_cache(
    db: Session = Depends(get_db),
    organization: schemas.Organization = Depends(get_organization_from_api_key)
):
    """
    Clear all cache entries for the organization.
    
    This will delete all cached LLM responses from both Redis and PostgreSQL.
    Use with caution.
    """
    # Clear Redis cache for this organization only
    redis_deleted, postgres_deleted = cache_service.clear_for_org(db, organization.id)
    
    return {
        "message": "Cache cleared successfully",
        "redis_entries_deleted": redis_deleted,
        "postgres_entries_deleted": postgres_deleted
    }


@router.delete("/entry/{cache_key}")
def delete_cache_entry(
    cache_key: str,
    db: Session = Depends(get_db),
    organization: schemas.Organization = Depends(get_organization_from_api_key)
):
    """
    Delete a specific cache entry by key.
    
    Args:
    - cache_key: The MD5 hash of the cached request
    """
    if ":" in cache_key:
        org_scoped_cache_key = cache_key
    else:
        org_scoped_cache_key = f"{organization.id}:{cache_key}"
    
    cache_entry = crud.get_from_cache(db, org_scoped_cache_key, organization.id)
    if not cache_entry:
        raise HTTPException(status_code=404, detail="Cache entry not found")
    
    cache_service.delete_entry(db, organization.id, org_scoped_cache_key)
    
    return {
        "message": "Cache entry deleted successfully",
        "cache_key": org_scoped_cache_key
    }
