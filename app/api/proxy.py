"""
Core LLM proxy endpoint with caching and multi-provider routing.
"""
import time
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from .. import crud, schemas
from ..database import get_db
from ..security import get_organization_from_api_key
from ..services.router import ProviderRouter
from ..services.tokens import count_messages_tokens
from ..services.pricing import calculate_cost
from ..services.redis_cache import redis_cache
from ..services.rate_limiter import RateLimiter


router = APIRouter(tags=["proxy"])


@router.post("/v1/chat/completions", response_model=schemas.ChatCompletionResponse)
async def chat_completions(
    request: schemas.ChatCompletionRequest,
    response: Response,
    db: Session = Depends(get_db),
    organization: schemas.Organization = Depends(get_organization_from_api_key)
):
    """
    OpenAI-compatible chat completions endpoint with caching and multi-provider routing.
    
    Features:
    - Automatic response caching (30-70% cost savings)
    - Multi-provider routing (OpenAI, Anthropic, Mistral, Groq)
    - Token counting and cost calculation
    - Request logging and analytics
    - Fallback to alternative providers on failure
    - Rate limiting per organization (100 req/min default)
    
    Usage:
    ```python
    from openai import OpenAI
    
    client = OpenAI(
        api_key="your-cognitude-key",
        base_url="http://your-server:8000/v1"
    )
    
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": "Hello!"}]
    )
    ```
    
    Rate Limiting:
    - Default: 100 requests/minute, 3000 requests/hour, 50k requests/day
    - Configurable via /rate-limits/config endpoint
    - Returns 429 status when limit exceeded
    - Rate limit headers included in all responses:
      - X-RateLimit-Limit: Total requests allowed per minute
      - X-RateLimit-Remaining: Requests remaining in current minute
      - X-RateLimit-Reset: Unix timestamp when limit resets
    ```
    """
    start_time = time.time()
    
    # Check rate limits FIRST (before any processing)
    rate_limiter = RateLimiter(redis_cache, db)
    is_allowed, retry_after, usage = rate_limiter.check_rate_limit(organization.id)
    
    # Add rate limit headers to response
    headers = rate_limiter.get_rate_limit_headers(organization.id, usage)
    for header, value in headers.items():
        response.headers[header] = value
    
    # Return 429 if rate limited
    if not is_allowed:
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded. Retry after {retry_after} seconds.",
            headers={"Retry-After": str(retry_after)}
        )
    
    # Convert messages to dict format for caching
    messages_dict = [{"role": msg.role, "content": msg.content} for msg in request.messages]
    
    # Generate cache key
    cache_key = crud.generate_cache_key(
        request.model,
        messages_dict,
        request.temperature,
        request.max_tokens
    )
    
    # Check cache first (Redis → PostgreSQL fallback)
    cached_response = None
    
    # Try Redis cache first (fast <10ms)
    redis_cached = redis_cache.get(cache_key, organization.id)
    if redis_cached:
        cached_response = type('obj', (object,), {
            'response_data': redis_cached['response_data'],
            'provider': redis_cached['provider'],
            'prompt_tokens': redis_cached['prompt_tokens'],
            'completion_tokens': redis_cached['completion_tokens'],
            'cost_usd': redis_cached['cost_usd']
        })()
    else:
        # Fallback to PostgreSQL cache
        cached_response = crud.get_from_cache(db, cache_key, organization.id)
    
    if cached_response:
        # Cache hit! Return cached response
        latency_ms = int((time.time() - start_time) * 1000)
        
        # Parse cached response
        response_data = cached_response.response_data
        
        # Add metadata
        response_data["cached"] = True
        response_data["provider"] = cached_response.provider
        response_data["cost_usd"] = float(cached_response.cost_usd)
        
        # Log the request (cache hit, no cost)
        crud.log_llm_request(
            db=db,
            organization_id=organization.id,
            model=request.model,
            provider=cached_response.provider,
            prompt_tokens=cached_response.prompt_tokens,
            completion_tokens=cached_response.completion_tokens,
            total_tokens=cached_response.prompt_tokens + cached_response.completion_tokens,
            cost_usd=0,  # No cost for cached response
            latency_ms=latency_ms,
            cached=True,
            cache_key=cache_key
        )
        
        return response_data
    
    # Cache miss - call provider
    provider_router = ProviderRouter(db, organization.id)
    
    # Select provider based on model
    provider_config = provider_router.select_provider(request.model)
    
    if not provider_config:
        raise HTTPException(
            status_code=400,
            detail=f"No provider configured for model '{request.model}'. Please configure a provider first."
        )
    
    # Prepare request parameters
    request_params = {
        "temperature": request.temperature,
        "max_tokens": request.max_tokens,
        "top_p": request.top_p,
        "frequency_penalty": request.frequency_penalty,
        "presence_penalty": request.presence_penalty,
        "stop": request.stop,
        "n": request.n,
    }
    
    # Remove None values
    request_params = {k: v for k, v in request_params.items() if v is not None}
    
    try:
        # Call provider with fallback
        response_data = await provider_router.call_with_fallback(
            model=request.model,
            messages=messages_dict,
            **request_params
        )
        
        # Extract usage info
        usage = response_data["usage"]
        prompt_tokens = usage["prompt_tokens"]
        completion_tokens = usage["completion_tokens"]
        total_tokens = usage["total_tokens"]
        
        # Calculate cost
        cost_usd = calculate_cost(request.model, prompt_tokens, completion_tokens)
        
        # Calculate latency
        latency_ms = int((time.time() - start_time) * 1000)
        
        # Store in both Redis (hot cache) and PostgreSQL (cold storage)
        # Redis first for speed
        redis_cache.set(
            cache_key=cache_key,
            organization_id=organization.id,
            response_data=response_data,
            model=request.model,
            provider=provider_config.provider,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            cost_usd=float(cost_usd),
            ttl_hours=24
        )
        
        # PostgreSQL for analytics and persistence
        crud.store_in_cache(
            db=db,
            organization_id=organization.id,
            cache_key=cache_key,
            model=request.model,
            provider=provider_config.provider,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            cost_usd=cost_usd,
            response_data=response_data
        )
        
        # Log the request
        crud.log_llm_request(
            db=db,
            organization_id=organization.id,
            model=request.model,
            provider=provider_config.provider,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            cost_usd=cost_usd,
            latency_ms=latency_ms,
            cached=False,
            cache_key=cache_key
        )
        
        # Add metadata to response
        response_data["cached"] = False
        response_data["provider"] = provider_config.provider
        response_data["cost_usd"] = float(cost_usd)
        
        return response_data
        
    except Exception as e:
        # Log failed request
        latency_ms = int((time.time() - start_time) * 1000)
        
        # Try to count tokens even on failure
        try:
            prompt_tokens = count_messages_tokens(messages_dict, request.model)
        except:
            prompt_tokens = 0
        
        crud.log_llm_request(
            db=db,
            organization_id=organization.id,
            model=request.model,
            provider=provider_config.provider if provider_config else "unknown",
            prompt_tokens=prompt_tokens,
            completion_tokens=0,
            total_tokens=prompt_tokens,
            cost_usd=0,
            latency_ms=latency_ms,
            cached=False,
            cache_key=None,
            error=str(e)
        )
        
        raise HTTPException(
            status_code=500,
            detail=f"LLM provider error: {str(e)}"
        )


@router.get("/v1/models")
async def list_models(
    db: Session = Depends(get_db),
    organization: schemas.Organization = Depends(get_organization_from_api_key)
):
    """
    List available models based on configured providers.
    OpenAI-compatible endpoint.
    """
    provider_router = ProviderRouter(db, organization.id)
    providers = provider_router.get_providers(enabled_only=True)
    
    # Build list of available models based on providers
    models_list = []
    
    for provider in providers:
        if provider.provider == "openai":
            models_list.extend([
                {"id": "gpt-4", "object": "model", "owned_by": "openai"},
                {"id": "gpt-4-turbo", "object": "model", "owned_by": "openai"},
                {"id": "gpt-3.5-turbo", "object": "model", "owned_by": "openai"},
            ])
        elif provider.provider == "anthropic":
            models_list.extend([
                {"id": "claude-3-opus", "object": "model", "owned_by": "anthropic"},
                {"id": "claude-3-sonnet", "object": "model", "owned_by": "anthropic"},
                {"id": "claude-3-haiku", "object": "model", "owned_by": "anthropic"},
            ])
        elif provider.provider == "mistral":
            models_list.extend([
                {"id": "mistral-large", "object": "model", "owned_by": "mistral"},
                {"id": "mistral-medium", "object": "model", "owned_by": "mistral"},
            ])
        elif provider.provider == "groq":
            models_list.extend([
                {"id": "llama3-70b", "object": "model", "owned_by": "groq"},
                {"id": "mixtral-8x7b", "object": "model", "owned_by": "groq"},
            ])
    
    return {
        "object": "list",
        "data": models_list
    }
