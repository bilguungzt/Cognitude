from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple

from sqlalchemy.orm import Session

from app import crud, schemas
from app.config import get_settings
from app.core.cache_keys import CacheKeyBuilder
from app.services.redis_cache import RedisCache, redis_cache


@dataclass
class CacheHit:
    cache_key: str
    payload: Dict[str, Any]


class CacheService:
    """
    Single source of truth for cache key construction and persistence across
    Redis and PostgreSQL backends.
    """

    def __init__(self, redis_cache: RedisCache):
        self.redis_cache = redis_cache
        settings = get_settings()
        self.ttl_hours = getattr(settings, "CACHE_TTL_HOURS", 24)

    def build_key(
        self,
        organization_id: int,
        request: schemas.ChatCompletionRequest,
        *,
        model_override: Optional[str] = None,
        extra_metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        return CacheKeyBuilder.chat_completion_key(
            organization_id,
            request,
            model_override=model_override,
            extra_metadata=extra_metadata,
        )

    def get_response(
        self,
        db: Session,
        organization_id: int,
        request: schemas.ChatCompletionRequest,
        *,
        model_override: Optional[str] = None,
        extra_metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[CacheHit]:
        cache_key = self.build_key(
            organization_id,
            request,
            model_override=model_override,
            extra_metadata=extra_metadata,
        )

        cached = self.redis_cache.get(
            organization_id,
            request,
            model_override=model_override,
            extra_metadata=extra_metadata,
        )
        if cached:
            cached.setdefault("response_data", {})
            return CacheHit(cache_key=cache_key, payload=cached)

        db_entry = crud.get_from_cache(
            db, cache_key=cache_key, organization_id=organization_id
        )
        if db_entry:
            return CacheHit(
                cache_key=cache_key,
                payload={
                    "response_data": db_entry.response_json,
                    "model": db_entry.model,
                    "provider": db_entry.response_json.get("x-cognitude", {}).get(
                        "provider", "unknown"
                    ),
                    "prompt_tokens": db_entry.response_json.get("usage", {}).get(
                        "prompt_tokens", 0
                    ),
                    "completion_tokens": db_entry.response_json.get("usage", {}).get(
                        "completion_tokens", 0
                    ),
                    "cost_usd": db_entry.response_json.get("x-cognitude", {}).get(
                        "cost", 0.0
                    ),
                },
            )

        return None

    def set_response(
        self,
        db: Session,
        organization_id: int,
        request: schemas.ChatCompletionRequest,
        response_data: Dict[str, Any],
        *,
        model: str,
        provider: str,
        prompt_tokens: int,
        completion_tokens: int,
        cost_usd: float,
        model_override: Optional[str] = None,
        extra_metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        cache_key = self.build_key(
            organization_id,
            request,
            model_override=model_override,
            extra_metadata=extra_metadata,
        )

        prompt_hash = CacheKeyBuilder.prompt_hash(request)
        crud.store_in_cache(
            db=db,
            organization_id=organization_id,
            cache_key=cache_key,
            prompt_hash=prompt_hash,
            model=model,
            response_json=response_data,
            ttl_hours=self.ttl_hours,
        )

        self.redis_cache.set(
            organization_id,
            request,
            response_data,
            model=model,
            provider=provider,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            cost_usd=cost_usd,
            ttl_hours=self.ttl_hours,
            model_override=model_override,
            extra_metadata=extra_metadata,
        )

        return cache_key

    def delete_entry(
        self,
        db: Session,
        organization_id: int,
        cache_key: str,
    ) -> None:
        crud_entry = crud.get_from_cache(
            db, cache_key=cache_key, organization_id=organization_id
        )
        if crud_entry:
            db.delete(crud_entry)
            db.commit()
        self.redis_cache.delete(organization_id, cache_key)

    def clear_for_org(self, db: Session, organization_id: int) -> Tuple[int, int]:
        redis_deleted = self.redis_cache.clear(organization_id)
        postgres_deleted = crud.clear_cache_for_org(db, organization_id)
        return redis_deleted, postgres_deleted


cache_service = CacheService(redis_cache)

