"""
Redis-based caching service for LLM responses.
Provides fast cache lookups (<10ms) with automatic TTL expiration.
"""
import redis
import json
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

from app.config import get_settings

settings = get_settings()


class RedisCache:
    """
    Redis cache manager for LLM responses.
    
    Features:
    - Fast lookups (<10ms vs PostgreSQL ~50ms)
    - Automatic TTL expiration (24 hours default)
    - Hit counter tracking
    - Fallback to PostgreSQL if Redis unavailable
    """
    
    def __init__(self):
        """Initialize Redis connection."""
        self.redis = None
        self.available = False
        
        # Try Upstash Redis first if token is provided
        if settings.REDIS_TOKEN and settings.REDIS_URL:
            try:
                from upstash_redis import Redis as UpstashRedis
                self.redis = UpstashRedis(
                    url=str(settings.REDIS_URL),
                    token=str(settings.REDIS_TOKEN)
                )
                # Test connection
                self.redis.ping()
                self.available = True
                print("✅ Upstash Redis connected successfully")
                return
            except Exception as e:
                print(f"❌ Upstash Redis connection failed: {e}")
                self.redis = None
                self.available = False
        
        # Fallback to traditional Redis
        if settings.REDIS_URL and not self.available:
            try:
                import redis
                self.redis = redis.from_url(
                    str(settings.REDIS_URL),
                    decode_responses=True,
                    socket_timeout=2,
                    socket_connect_timeout=2
                )
                # Test connection
                self.redis.ping()
                self.available = True
                print("✅ Traditional Redis connected successfully")
            except (redis.ConnectionError, redis.TimeoutError) as e:
                print(f"❌ Traditional Redis connection failed: {e}")
                self.redis = None
                self.available = False
    
    def get(self, cache_key: str, organization_id: int) -> Optional[Dict[str, Any]]:
        """
        Get cached LLM response from Redis.
        
        Args:
            cache_key: MD5 hash of request parameters
            organization_id: Organization ID for isolation
            
        Returns:
            Cached response dict or None if not found
        """
        if not self.available or not self.redis:
            return None
        
        try:
            # Build Redis key with organization prefix
            redis_key = f"llm_cache:{organization_id}:{cache_key}"
            
            # Get cached data
            cached_data = self.redis.get(redis_key)
            
            if cached_data:
                # Increment hit counter
                self.redis.hincrby(f"cache_stats:{organization_id}:{cache_key}", "hits", 1)
                self.redis.hset(f"cache_stats:{organization_id}:{cache_key}", "last_accessed", datetime.utcnow().isoformat())
                
                return json.loads(cached_data)
            
            return None
            
        except Exception as e:
            # Log error but don't crash - fallback to PostgreSQL
            print(f"Redis GET error: {e}")
            return None
    
    def set(
        self, 
        cache_key: str, 
        organization_id: int, 
        response_data: Dict[str, Any],
        model: str,
        provider: str,
        prompt_tokens: int,
        completion_tokens: int,
        cost_usd: float,
        ttl_hours: int = 24
    ) -> bool:
        """
        Store LLM response in Redis cache.
        
        Args:
            cache_key: MD5 hash of request parameters
            organization_id: Organization ID for isolation
            response_data: Full LLM response to cache
            model: Model name
            provider: Provider name
            prompt_tokens: Input token count
            completion_tokens: Output token count
            cost_usd: Request cost
            ttl_hours: Time to live in hours (default 24)
            
        Returns:
            True if cached successfully, False otherwise
        """
        if not self.available or not self.redis:
            return False
        
        try:
            redis_key = f"llm_cache:{organization_id}:{cache_key}"
            
            # Store response data with TTL
            cache_entry = {
                "response_data": response_data,
                "model": model,
                "provider": provider,
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "cost_usd": cost_usd,
                "cached_at": datetime.utcnow().isoformat()
            }
            
            self.redis.setex(
                redis_key,
                timedelta(hours=ttl_hours),
                json.dumps(cache_entry)
            )
            
            # Initialize stats counter
            stats_key = f"cache_stats:{organization_id}:{cache_key}"
            self.redis.hset(stats_key, "hits", 0)
            self.redis.hset(stats_key, "created_at", datetime.utcnow().isoformat())
            self.redis.expire(stats_key, timedelta(hours=ttl_hours))
            
            return True
            
        except Exception as e:
            print(f"Redis SET error: {e}")
            return False
    
    def get_stats(self, organization_id: int) -> Dict[str, Any]:
        """
        Get cache statistics for an organization.
        
        Args:
            organization_id: Organization ID
            
        Returns:
            Cache statistics dict
        """
        if not self.available or not self.redis:
            return {
                "redis_available": False,
                "total_entries": 0,
                "total_hits": 0
            }
        
        try:
            # Count cache entries for organization
            pattern = f"llm_cache:{organization_id}:*"
            keys = list(self.redis.scan_iter(match=pattern, count=100))
            
            total_hits = 0
            for key in keys:
                cache_key = key.split(":")[-1]
                stats_key = f"cache_stats:{organization_id}:{cache_key}"
                hits = self.redis.hget(stats_key, "hits")
                if hits:
                    total_hits += int(hits)
            
            return {
                "redis_available": True,
                "total_entries": len(keys),
                "total_hits": total_hits
            }
            
        except Exception as e:
            print(f"Redis STATS error: {e}")
            return {
                "redis_available": False,
                "error": str(e)
            }
    
    def clear(self, organization_id: int) -> int:
        """
        Clear all cache entries for an organization.
        
        Args:
            organization_id: Organization ID
            
        Returns:
            Number of entries deleted
        """
        if not self.available or not self.redis:
            return 0
        
        try:
            # Find all cache keys for organization
            pattern = f"llm_cache:{organization_id}:*"
            keys = list(self.redis.scan_iter(match=pattern, count=100))
            
            # Also delete stats keys
            stats_pattern = f"cache_stats:{organization_id}:*"
            stats_keys = list(self.redis.scan_iter(match=stats_pattern, count=100))
            
            all_keys = keys + stats_keys
            
            if all_keys:
                return self.redis.delete(*all_keys)
            
            return 0
            
        except Exception as e:
            print(f"Redis CLEAR error: {e}")
            return 0
    
    def health_check(self) -> Dict[str, Any]:
        """
        Check Redis connection health.
        
        Returns:
            Health status dict
        """
        if not self.available or not self.redis:
            return {
                "status": "unavailable",
                "message": "Redis connection not established"
            }
        
        try:
            self.redis.ping()
            info = self.redis.info()
            
            return {
                "status": "healthy",
                "connected_clients": info.get("connected_clients", 0),
                "used_memory_human": info.get("used_memory_human", "unknown"),
                "uptime_in_seconds": info.get("uptime_in_seconds", 0)
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }


# Global instance
redis_cache = RedisCache()
