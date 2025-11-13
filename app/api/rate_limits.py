"""
Rate limiting management API.

Endpoints for configuring and monitoring rate limits per organization.
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Response
import logging
from datetime import datetime
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from .. import schemas
from ..database import get_db
from ..security import get_organization_from_api_key
from ..models import RateLimitConfig
from ..services.redis_cache import RedisCache
from ..services.rate_limiter import RateLimiter


router = APIRouter(prefix="/rate-limits", tags=["rate-limits"])


# ============================================================================
# Schemas
# ============================================================================

class RateLimitConfigCreate(BaseModel):
    """Request schema for creating/updating rate limit config."""
    requests_per_minute: int = Field(default=100, ge=1, le=10000, description="Requests per minute limit")
    requests_per_hour: int = Field(default=3000, ge=1, le=1000000, description="Requests per hour limit")
    requests_per_day: int = Field(default=50000, ge=1, le=10000000, description="Requests per day limit")
    enabled: bool = Field(default=True, description="Enable rate limiting")
    
    class Config:
        json_schema_extra = {
            "example": {
                "requests_per_minute": 100,
                "requests_per_hour": 3000,
                "requests_per_day": 50000,
                "enabled": True
            }
        }


class RateLimitConfigResponse(BaseModel):
    """Response schema for rate limit config."""
    id: int
    organization_id: int
    requests_per_minute: int
    requests_per_hour: int
    requests_per_day: int
    enabled: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class RateLimitUsageResponse(BaseModel):
    """Response schema for current usage."""
    minute: dict
    hour: dict
    day: dict
    
    class Config:
        json_schema_extra = {
            "example": {
                "minute": {"used": 45, "limit": 100, "remaining": 55},
                "hour": {"used": 1234, "limit": 3000, "remaining": 1766},
                "day": {"used": 15678, "limit": 50000, "remaining": 34322}
            }
        }


# ============================================================================
# Endpoints
# ============================================================================

@router.get("/config", response_model=RateLimitConfigResponse)
def get_rate_limit_config(
    db: Session = Depends(get_db),
    organization: schemas.Organization = Depends(get_organization_from_api_key)
):
    """
    Get current rate limit configuration for your organization.
    
    Returns the configured limits for minute/hour/day windows. If no custom
    configuration exists, returns the default limits.
    
    **Default Limits:**
    - Minute: 100 requests
    - Hour: 3,000 requests
    - Day: 50,000 requests
    
    **Response:**
    ```json
    {
      "id": 1,
      "organization_id": 123,
      "requests_per_minute": 100,
      "requests_per_hour": 3000,
      "requests_per_day": 50000,
      "enabled": true,
      "created_at": "2025-11-10T14:30:00Z",
      "updated_at": "2025-11-10T14:30:00Z"
    }
    ```
    """
    try:
        config = db.query(RateLimitConfig).filter(
            RateLimitConfig.organization_id == organization.id
        ).first()

        if not config:
            # Create default config if it doesn't exist
            config = RateLimitConfig(
                organization_id=organization.id,
                requests_per_minute=100,
                requests_per_hour=3000,
                requests_per_day=50000,
                enabled=True
            )
            db.add(config)
            db.commit()
            db.refresh(config)

        return config

    except OperationalError as e:
        # Common in environments where migrations haven't been applied.
        logging.warning(f"Database operational error when fetching rate limit config: {e}")
        # Return a sensible default response so callers (UI) don't crash.
        now_iso = datetime.utcnow().isoformat() + "Z"
        return {
            "id": 0,
            "organization_id": organization.id,
            "requests_per_minute": 100,
            "requests_per_hour": 3000,
            "requests_per_day": 50000,
            "enabled": True,
            "created_at": now_iso,
            "updated_at": now_iso,
        }
    except Exception as e:
        logging.exception("Unexpected error in get_rate_limit_config")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/config", response_model=RateLimitConfigResponse)
def update_rate_limit_config(
    config_data: RateLimitConfigCreate,
    db: Session = Depends(get_db),
    organization: schemas.Organization = Depends(get_organization_from_api_key)
):
    """
    Update rate limit configuration for your organization.
    
    Customize your rate limits based on your usage patterns. Higher limits
    allow more requests but may incur higher costs.
    
    **Parameters:**
    - `requests_per_minute`: 1-10,000 requests per minute
    - `requests_per_hour`: 1-1,000,000 requests per hour
    - `requests_per_day`: 1-10,000,000 requests per day
    - `enabled`: Enable/disable rate limiting
    
    **Request:**
    ```json
    {
      "requests_per_minute": 200,
      "requests_per_hour": 6000,
      "requests_per_day": 100000,
      "enabled": true
    }
    ```
    
    **Response:**
    Returns the updated configuration with timestamps.
    
    **Note:** Changes take effect immediately. Existing rate limit counters
    are not reset - they will continue counting against the new limits.
    """
    try:
        config = db.query(RateLimitConfig).filter(
            RateLimitConfig.organization_id == organization.id
        ).first()

        if not config:
            # Create new config
            config = RateLimitConfig(
                organization_id=organization.id,
                requests_per_minute=config_data.requests_per_minute,
                requests_per_hour=config_data.requests_per_hour,
                requests_per_day=config_data.requests_per_day,
                enabled=config_data.enabled
            )
            db.add(config)
        else:
            # Update existing config
            update_data = config_data.model_dump(exclude_unset=True)
            for key, value in update_data.items():
                setattr(config, key, value)

        db.commit()
        db.refresh(config)

        return config

    except OperationalError as e:
        logging.warning(f"Database operational error when updating rate limit config: {e}")
        raise HTTPException(status_code=503, detail="Database schema not available. Apply migrations and try again.")
    except Exception as e:
        logging.exception("Unexpected error in update_rate_limit_config")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/usage", response_model=RateLimitUsageResponse)
def get_rate_limit_usage(
    db: Session = Depends(get_db),
    organization: schemas.Organization = Depends(get_organization_from_api_key)
):
    """
    Get current rate limit usage for your organization.
    
    Shows how many requests you've made in the current minute/hour/day
    windows, along with your limits and remaining quota.
    
    **Response:**
    ```json
    {
      "minute": {
        "used": 45,
        "limit": 100,
        "remaining": 55
      },
      "hour": {
        "used": 1234,
        "limit": 3000,
        "remaining": 1766
      },
      "day": {
        "used": 15678,
        "limit": 50000,
        "remaining": 34322
      }
    }
    ```
    
    **Use Cases:**
    - Monitor current usage before making batch requests
    - Display quota in your application dashboard
    - Implement client-side rate limiting
    - Debug rate limit errors (429 responses)
    """
    # Initialize rate limiter
    redis_cache = RedisCache()
    rate_limiter = RateLimiter(redis_cache, db)
    
    # Get current usage without incrementing
    usage = rate_limiter.get_current_usage(organization.id)
    
    return usage


@router.post("/reset")
def reset_rate_limits(
    db: Session = Depends(get_db),
    organization: schemas.Organization = Depends(get_organization_from_api_key)
):
    """
    Reset rate limit counters for your organization.
    
    This is an admin/emergency function that resets all current rate limit
    counters to zero. Use with caution - this allows immediate retry of
    requests that were previously rate limited.
    
    **Use Cases:**
    - Testing rate limit behavior
    - Emergency override after false positives
    - Debugging rate limit issues
    
    **Response:**
    ```json
    {
      "message": "Rate limits reset successfully",
      "organization_id": 123
    }
    ```
    
    **Note:** This only resets the current counters. Rate limiting will
    resume immediately with the next request. To disable rate limiting
    entirely, use PUT /rate-limits/config with enabled=false.
    """
    # Initialize rate limiter
    redis_cache = RedisCache()
    rate_limiter = RateLimiter(redis_cache, db)
    
    # Reset limits
    success = rate_limiter.reset_limits(organization.id)
    
    if not success:
        raise HTTPException(
            status_code=500,
            detail="Failed to reset rate limits. Redis may be unavailable."
        )
    
    return {
        "message": "Rate limits reset successfully",
        "organization_id": organization.id
    }


@router.delete("/config")
def delete_rate_limit_config(
    db: Session = Depends(get_db),
    organization: schemas.Organization = Depends(get_organization_from_api_key)
):
    """
    Delete rate limit configuration and revert to defaults.
    
    Removes your custom rate limit configuration. Your organization will
    revert to the default limits:
    - Minute: 100 requests
    - Hour: 3,000 requests
    - Day: 50,000 requests
    
    **Response:**
    ```json
    {
      "message": "Rate limit configuration deleted. Reverted to default limits.",
      "organization_id": 123
    }
    ```
    """
    try:
        config = db.query(RateLimitConfig).filter(
            RateLimitConfig.organization_id == organization.id
        ).first()

        if config:
            db.delete(config)
            db.commit()
            return {
                "message": "Rate limit configuration deleted. Reverted to default limits.",
                "organization_id": organization.id
            }

        return {
            "message": "No custom configuration found. Already using default limits.",
            "organization_id": organization.id
        }

    except OperationalError as e:
        logging.warning(f"Database operational error when deleting rate limit config: {e}")
        raise HTTPException(status_code=503, detail="Database schema not available. Apply migrations and try again.")
    except Exception:
        logging.exception("Unexpected error in delete_rate_limit_config")
        raise HTTPException(status_code=500, detail="Internal server error")
