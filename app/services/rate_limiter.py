"""
Rate limiting service using Redis for distributed rate limiting.

This module provides:
- Per-organization rate limiting
- Multiple time windows (minute/hour/day)
- Redis-backed counters for distributed systems
- Graceful degradation if Redis unavailable
- Rate limit headers in responses
"""
import time
import logging
from typing import Optional, Tuple, Dict
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
import sqlalchemy as sa

from ..models import RateLimitConfig
from .redis_cache import RedisCache

logger = logging.getLogger(__name__)


class RateLimiter:
    """
    Redis-backed rate limiter with multiple time windows.
    
    Features:
    - Distributed rate limiting across multiple API instances
    - Per-organization configurable limits
    - Minute, hour, and day windows
    - Atomic increment operations
    - Automatic key expiration
    - Graceful degradation if Redis unavailable
    
    Usage:
    ```python
    limiter = RateLimiter(redis_cache, db)
    is_allowed, retry_after = limiter.check_rate_limit(org_id)
    
    if not is_allowed:
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded. Retry after {retry_after} seconds.",
            headers={"Retry-After": str(retry_after)}
        )
    ```
    """
    
    def __init__(self, redis_cache: RedisCache, db: Session):
        """
        Initialize rate limiter.
        
        Args:
            redis_cache: Redis cache instance for storing counters
            db: Database session for fetching rate limit configs
        """
        self.redis = redis_cache
        self.db = db
        self._default_limits = {
            "minute": 100,
            "hour": 3000,
            "day": 50000
        }
    
    def _get_rate_limit_config(self, organization_id: int) -> Dict[str, int]:
        """
        Get rate limit configuration for organization.
        
        Args:
            organization_id: Organization ID
            
        Returns:
            Dict with minute/hour/day limits
        """
        try:
            # Use a select statement to fetch raw column values, bypassing ORM attribute issues.
            stmt = sa.select(
                RateLimitConfig.requests_per_minute,
                RateLimitConfig.requests_per_hour,
                RateLimitConfig.requests_per_day
            ).where(
                RateLimitConfig.organization_id == organization_id,
                RateLimitConfig.enabled == True
            )
            result = self.db.execute(stmt).first()
            
            if result:
                return {
                    "minute": result.requests_per_minute,
                    "hour": result.requests_per_hour,
                    "day": result.requests_per_day
                }
            
            # Return defaults if no config found
            return self._default_limits
            
        except Exception as e:
            logger.warning(f"Error fetching rate limit config for org {organization_id}: {e}")
            return self._default_limits
    
    def _get_current_window_key(self, organization_id: int, window: str) -> str:
        """
        Generate Redis key for current time window.
        
        Args:
            organization_id: Organization ID
            window: Time window (minute/hour/day)
            
        Returns:
            Redis key string
        """
        now = datetime.utcnow()
        
        if window == "minute":
            # Key: rate_limit:org_123:minute:2025-11-10:14:30
            window_str = now.strftime("%Y-%m-%d:%H:%M")
        elif window == "hour":
            # Key: rate_limit:org_123:hour:2025-11-10:14
            window_str = now.strftime("%Y-%m-%d:%H")
        else:  # day
            # Key: rate_limit:org_123:day:2025-11-10
            window_str = now.strftime("%Y-%m-%d")
        
        return f"rate_limit:org_{organization_id}:{window}:{window_str}"
    
    def _get_window_expiry(self, window: str) -> int:
        """
        Get TTL for rate limit window in seconds.
        
        Args:
            window: Time window (minute/hour/day)
            
        Returns:
            TTL in seconds
        """
        if window == "minute":
            return 120  # 2 minutes (buffer for clock skew)
        elif window == "hour":
            return 7200  # 2 hours
        else:  # day
            return 172800  # 2 days
    
    def _check_window(
        self,
        organization_id: int,
        window: str,
        limit: int
    ) -> Tuple[bool, int, int]:
        """
        Check rate limit for a specific time window.

        Args:
            organization_id: Organization ID
            window: Time window (minute/hour/day)
            limit: Request limit for this window

        Returns:
            Tuple of (is_allowed, current_count, retry_after_seconds)
        """
        if not self.redis.redis:
            # Redis unavailable - use in-memory fallback
            logger.warning(f"Redis unavailable for rate limiting org {organization_id}, using in-memory fallback")
            return self._check_window_in_memory(organization_id, window, limit)

        try:
            key = self._get_current_window_key(organization_id, window)

            # Atomic increment with pipeline
            pipe = self.redis.redis.pipeline()
            pipe.incr(key)
            pipe.expire(key, self._get_window_expiry(window))
            results = pipe.execute()

            current_count = results[0]

            # Check if limit exceeded
            if current_count > limit:
                # Calculate retry_after based on window
                now = datetime.utcnow()
                if window == "minute":
                    next_window = (now + timedelta(minutes=1)).replace(second=0, microsecond=0)
                elif window == "hour":
                    next_window = (now + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
                else:  # day
                    next_window = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)

                retry_after = int((next_window - now).total_seconds()) + 1
                return False, current_count, retry_after

            return True, current_count, 0

        except Exception as e:
            logger.error(f"Rate limit check error for org {organization_id}, window {window}: {e}")
            # On error, fall back to in-memory rate limiting
            return self._check_window_in_memory(organization_id, window, limit)

    def _check_window_in_memory(
        self,
        organization_id: int,
        window: str,
        limit: int
    ) -> Tuple[bool, int, int]:
        """
        In-memory fallback for rate limiting when Redis is unavailable.

        Args:
            organization_id: Organization ID
            window: Time window (minute/hour/day)
            limit: Request limit for this window

        Returns:
            Tuple of (is_allowed, current_count, retry_after_seconds)
        """
        # Simple in-memory storage using class-level dictionary
        if not hasattr(self, '_in_memory_storage'):
            self._in_memory_storage = {}

        now = datetime.utcnow()
        key = f"{organization_id}:{window}:{self._get_window_key(now, window)}"

        # Initialize storage for this window if needed
        if key not in self._in_memory_storage:
            self._in_memory_storage[key] = {
                'count': 0,
                'expires_at': self._get_window_expiry_time(now, window)
            }

        # Clean up expired entries periodically
        self._cleanup_in_memory_storage()

        # Increment counter
        self._in_memory_storage[key]['count'] += 1
        current_count = self._in_memory_storage[key]['count']

        # Check if limit exceeded
        if current_count > limit:
            retry_after = int((self._in_memory_storage[key]['expires_at'] - now).total_seconds()) + 1
            return False, current_count, retry_after

        return True, current_count, 0

    def _get_window_key(self, dt: datetime, window: str) -> str:
        """Get the key for a given datetime and window."""
        if window == "minute":
            return dt.strftime("%Y-%m-%d:%H:%M")
        elif window == "hour":
            return dt.strftime("%Y-%m-%d:%H")
        else:  # day
            return dt.strftime("%Y-%m-%d")

    def _get_window_expiry_time(self, dt: datetime, window: str) -> datetime:
        """Get the expiry time for a given window."""
        if window == "minute":
            return (dt + timedelta(minutes=1)).replace(second=0, microsecond=0)
        elif window == "hour":
            return (dt + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
        else:  # day
            return (dt + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)

    def _cleanup_in_memory_storage(self):
        """Clean up expired entries from in-memory storage."""
        if not hasattr(self, '_in_memory_storage'):
            return

        now = datetime.utcnow()
        expired_keys = [
            key for key, data in self._in_memory_storage.items()
            if data['expires_at'] < now
        ]

        for key in expired_keys:
            del self._in_memory_storage[key]
    
    def check_rate_limit(
        self,
        organization_id: int
    ) -> Tuple[bool, Optional[int], Dict[str, int]]:
        """
        Check rate limits across all time windows.

        Checks minute, hour, and day limits. If any window is exceeded,
        returns False with retry_after for the most restrictive window.
        Falls back to in-memory rate limiting if Redis is unavailable.

        Args:
            organization_id: Organization ID to check

        Returns:
            Tuple of (is_allowed, retry_after_seconds, usage_dict)
            where usage_dict contains current counts for each window
        """
        # Get limits for this organization
        limits = self._get_rate_limit_config(organization_id)

        # Check all windows
        usage = {}
        retry_after = None
        is_allowed = True

        for window in ["minute", "hour", "day"]:
            limit = limits[window]
            allowed, count, retry = self._check_window(organization_id, window, limit)

            usage[window] = count

            if not allowed:
                is_allowed = False
                # Use shortest retry_after (most restrictive)
                if retry_after is None or retry < retry_after:
                    retry_after = retry

        return is_allowed, retry_after, usage
    
    def get_rate_limit_headers(
        self,
        organization_id: int,
        usage: Dict[str, int]
    ) -> Dict[str, str]:
        """
        Generate X-RateLimit headers for response.
        
        Args:
            organization_id: Organization ID
            usage: Current usage counts from check_rate_limit()
            
        Returns:
            Dict of headers to add to response
        """
        limits = self._get_rate_limit_config(organization_id)
        
        # Use minute window for headers (most common convention)
        limit = limits["minute"]
        remaining = max(0, limit - usage.get("minute", 0))
        
        # Calculate reset time (start of next minute)
        now = datetime.utcnow()
        next_minute = (now + timedelta(minutes=1)).replace(second=0, microsecond=0)
        reset_timestamp = int(next_minute.timestamp())
        
        return {
            "X-RateLimit-Limit": str(limit),
            "X-RateLimit-Remaining": str(remaining),
            "X-RateLimit-Reset": str(reset_timestamp)
        }
    
    def get_current_usage(self, organization_id: int) -> Dict[str, Dict[str, int]]:
        """
        Get current usage across all time windows without incrementing.
        
        Args:
            organization_id: Organization ID
            
        Returns:
            Dict with usage and limits for each window
        """
        if not self.redis.redis:
            return {
                "minute": {"used": 0, "limit": self._default_limits["minute"]},
                "hour": {"used": 0, "limit": self._default_limits["hour"]},
                "day": {"used": 0, "limit": self._default_limits["day"]}
            }
        
        limits = self._get_rate_limit_config(organization_id)
        result = {}
        
        try:
            for window in ["minute", "hour", "day"]:
                key = self._get_current_window_key(organization_id, window)
                count = self.redis.redis.get(key)
                used = int(count) if count else 0
                
                result[window] = {
                    "used": used,
                    "limit": limits[window],
                    "remaining": max(0, limits[window] - used)
                }
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting current usage for org {organization_id}: {e}")
            # Return default structure on error
            return {
                "minute": {"used": 0, "limit": limits["minute"]},
                "hour": {"used": 0, "limit": limits["hour"]},
                "day": {"used": 0, "limit": limits["day"]}
            }
    
    def reset_limits(self, organization_id: int) -> bool:
        """
        Reset rate limits for an organization (admin function).
        
        Args:
            organization_id: Organization ID
            
        Returns:
            True if reset successful
        """
        if not self.redis.redis:
            logger.warning("Redis unavailable for rate limit reset")
            return False
        
        try:
            now = datetime.utcnow()
            
            # Delete current window keys
            keys_to_delete = []
            
            # Minute key
            minute_key = self._get_current_window_key(organization_id, "minute")
            keys_to_delete.append(minute_key)
            
            # Hour key
            hour_key = self._get_current_window_key(organization_id, "hour")
            keys_to_delete.append(hour_key)
            
            # Day key
            day_key = self._get_current_window_key(organization_id, "day")
            keys_to_delete.append(day_key)
            
            # Delete all keys
            self.redis.redis.delete(*keys_to_delete)
            
            logger.info(f"Rate limits reset for organization {organization_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error resetting rate limits for org {organization_id}: {e}")
            return False
