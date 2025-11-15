"""
Redis-based caching service for LLM responses.
Provides fast cache lookups (<10ms) with automatic TTL expiration.
"""
import json
from typing import Optional, Dict, Any, Union
from datetime import datetime, timedelta

from app.config import get_settings
from app.core.cache_keys import CacheKeyBuilder
from app import schemas

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
        self.is_upstash = False
        
        # Try Upstash Redis first if token is provided
        if settings.REDIS_TOKEN and settings.REDIS_URL:
            try:
                from upstash_redis import Redis as UpstashRedis
                
                # Determine Upstash REST URL
                redis_url = str(settings.REDIS_URL).strip().strip('"').strip("'")
                print(f"DEBUG: Original REDIS_URL: {redis_url}")
                if redis_url.startswith("https://"):
                    # Already a REST URL
                    upstash_url = redis_url
                elif redis_url.startswith("rediss://") or redis_url.startswith("redis://"):
                    # Extract host from TCP URL for REST API
                    # Format: rediss://user:pass@host:port or redis://host:port
                    if "@" in redis_url:
                        host_part = redis_url.split("@")[-1].split(":")[0]
                    else:
                        host_part = redis_url.split("://")[-1].split(":")[0]
                    upstash_url = f"https://{host_part}"
                    print(f"DEBUG: Extracted host_part: {host_part}, upstash_url: {upstash_url}")
                else:
                    # Assume it's just host:port, add https://
                    upstash_url = f"https://{redis_url}"
                
                self.redis = UpstashRedis(
                    url=upstash_url,
                    token=str(settings.REDIS_TOKEN)
                )
                # Test connection
                self.redis.ping()
                self.available = True
                self.is_upstash = True
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
                redis_url = str(settings.REDIS_URL)
                
                # Ensure URL has proper scheme
                if not redis_url.startswith(("redis://", "rediss://", "unix://")):
                    if ":" in redis_url and not redis_url.startswith("http"):
                        # Assume host:port format, add redis://
                        redis_url = f"redis://{redis_url}"
                    else:
                        # Try as-is, might be malformed
                        pass
                
                self.redis = redis.from_url(
                    redis_url,
                    decode_responses=True,
                    socket_timeout=2,
                    socket_connect_timeout=2
                )
                # Test connection
                self.redis.ping()
                self.available = True
                self.is_upstash = False
                print("✅ Traditional Redis connected successfully")
            except (redis.ConnectionError, redis.TimeoutError, ValueError) as e:
                print(f"❌ Traditional Redis connection failed: {e}")
                self.redis = None
                self.available = False
    
    def _format_key(self, cache_key: str) -> str:
        return f"llm_cache:{cache_key}"

    def _resolve_cache_key(
        self,
        organization_id: int,
        request_or_key: Union[str, schemas.ChatCompletionRequest],
        *,
        model_override: Optional[str] = None,
        extra_metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        if isinstance(request_or_key, str):
            return request_or_key
        return CacheKeyBuilder.chat_completion_key(
            organization_id,
            request_or_key,
            model_override=model_override,
            extra_metadata=extra_metadata,
        )

    def get(
        self,
        organization_id: int,
        request_or_key: Union[str, schemas.ChatCompletionRequest],
        *,
        model_override: Optional[str] = None,
        extra_metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
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
            cache_key = self._resolve_cache_key(
                organization_id,
                request_or_key,
                model_override=model_override,
                extra_metadata=extra_metadata,
            )
            redis_key = self._format_key(cache_key)
            
            # Get cached data
            cached_data = self.redis.get(redis_key)
            
            if cached_data:
                # Parse the cached data
                if isinstance(cached_data, bytes):
                    cached_data = cached_data.decode('utf-8')
                
                # Increment hit counter
                self.redis.hincrby(f"cache_stats:{organization_id}:{cache_key}", "hits", 1)
                self.redis.hset(
                    f"cache_stats:{organization_id}:{cache_key}", 
                    "last_accessed", 
                    datetime.utcnow().isoformat()
                )
                
                return json.loads(cached_data)
            
            return None
            
        except Exception as e:
            # Log error but don't crash - fallback to PostgreSQL
            print(f"Redis GET error: {e}")
            return None
    
    def set(
        self,
        organization_id: int,
        request_or_key: Union[str, schemas.ChatCompletionRequest],
        response_data: Dict[str, Any],
        *,
        model: str,
        provider: str,
        prompt_tokens: int,
        completion_tokens: int,
        cost_usd: float,
        ttl_hours: int = 24,
        model_override: Optional[str] = None,
        extra_metadata: Optional[Dict[str, Any]] = None,
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
            cache_key = self._resolve_cache_key(
                organization_id,
                request_or_key,
                model_override=model_override,
                extra_metadata=extra_metadata,
            )
            redis_key = self._format_key(cache_key)
            
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
            
            # Calculate TTL in seconds
            ttl_seconds = int(timedelta(hours=ttl_hours).total_seconds())
            
            # Set with expiration
            self.redis.setex(
                redis_key,
                ttl_seconds,
                json.dumps(cache_entry)
            )
            
            # Initialize stats counter
            stats_key = f"cache_stats:{organization_id}:{cache_key}"
            self.redis.hset(stats_key, "hits", "0")
            self.redis.hset(stats_key, "created_at", datetime.utcnow().isoformat())
            self.redis.expire(stats_key, ttl_seconds)
            
            return True
            
        except Exception as e:
            print(f"Redis SET error: {e}")
            return False
    
    def delete(
        self,
        organization_id: int,
        request_or_key: Union[str, schemas.ChatCompletionRequest],
        *,
        model_override: Optional[str] = None,
        extra_metadata: Optional[Dict[str, Any]] = None,
    ) -> int:
        """
        Delete a specific cache entry.
        """
        if not self.available or not self.redis:
            return 0

        cache_key = self._resolve_cache_key(
            organization_id,
            request_or_key,
            model_override=model_override,
            extra_metadata=extra_metadata,
        )
        redis_key = self._format_key(cache_key)
        try:
            return int(self.redis.delete(redis_key) or 0)
        except Exception as e:
            print(f"Redis DELETE error: {e}")
            return 0

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
            
            # Different scan methods for Upstash vs traditional Redis
            if self.is_upstash:
                # Upstash may not support scan_iter, use keys() with caution
                try:
                    keys = self.redis.keys(pattern)
                except:
                    # Fallback: manual scan
                    keys = []
                    cursor = 0
                    while True:
                        cursor, partial_keys = self.redis.scan(cursor, match=pattern, count=100)
                        keys.extend(partial_keys)
                        if cursor == 0:
                            break
            else:
                # Traditional Redis with scan_iter
                keys = list(self.redis.scan_iter(match=pattern, count=100))
            
            total_hits = 0
            for key in keys:
                cache_key = key.split(":")[-1] if isinstance(key, str) else key.decode('utf-8').split(":")[-1]
                stats_key = f"cache_stats:{organization_id}:{cache_key}"
                hits = self.redis.hget(stats_key, "hits")
                if hits:
                    # Handle both string and bytes responses
                    if isinstance(hits, bytes):
                        hits = hits.decode('utf-8')
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
            stats_pattern = f"cache_stats:{organization_id}:*"
            
            # Different scan methods for Upstash vs traditional Redis
            if self.is_upstash:
                try:
                    keys = self.redis.keys(pattern)
                    stats_keys = self.redis.keys(stats_pattern)
                except:
                    # Fallback: manual scan
                    keys = []
                    cursor = 0
                    while True:
                        cursor, partial_keys = self.redis.scan(cursor, match=pattern, count=100)
                        keys.extend(partial_keys)
                        if cursor == 0:
                            break
                    
                    stats_keys = []
                    cursor = 0
                    while True:
                        cursor, partial_keys = self.redis.scan(cursor, match=stats_pattern, count=100)
                        stats_keys.extend(partial_keys)
                        if cursor == 0:
                            break
            else:
                keys = list(self.redis.scan_iter(match=pattern, count=100))
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
            
            # Upstash Redis may not support INFO command
            if self.is_upstash:
                return {
                    "status": "healthy",
                    "provider": "upstash",
                    "message": "Upstash Redis connection is healthy"
                }
            
            # Traditional Redis with INFO
            info = self.redis.info()
            
            return {
                "status": "healthy",
                "provider": "traditional",
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