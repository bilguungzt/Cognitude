"""
Cache management API endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import crud, schemas
from ..database import get_db
from ..security import get_organization_from_api_key
from ..services.redis_cache import redis_cache


router = APIRouter(prefix="/cache", tags=["cache"])


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
    
    # Get PostgreSQL stats (for comparison)
    pg_stats = crud.get_cache_stats(db, organization.id)
    
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
    # Clear Redis cache
    redis_cleared = redis_cache.clear(organization.id)
    
    # Clear PostgreSQL cache
    pg_cleared = crud.clear_cache(db, organization.id)
    
    return {
        "message": "Cache cleared successfully",
        "redis_entries_deleted": redis_cleared,
        "postgres_entries_deleted": pg_cleared
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
    # Get cache entry to verify ownership
    cache_entry = crud.get_from_cache(db, cache_key, organization.id)
    
    if not cache_entry:
        raise HTTPException(status_code=404, detail="Cache entry not found")
    
    # Delete the entry
    db.delete(cache_entry)
    db.commit()
    
    return {"message": "Cache entry deleted successfully"}
