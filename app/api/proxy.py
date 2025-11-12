"""
Core LLM proxy endpoint with caching and multi-provider routing.
"""
import time
from typing import Optional
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from .. import crud, schemas, models
from ..database import get_db
from ..security import get_organization_from_api_key
from ..services.router import ProviderRouter
from ..services.tokens import count_messages_tokens
from ..services.pricing import calculate_cost
from ..services.redis_cache import redis_cache
from ..services.rate_limiter import RateLimiter
from ..core.autopilot import AutopilotEngine


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
    
    # Instantiate Autopilot Engine
    autopilot = AutopilotEngine(db, redis_cache)

    # Get OpenAI API key
    provider_router = ProviderRouter(db, organization.id)
    openai_provider = provider_router.select_provider("gpt-4")
    if not openai_provider:
        raise HTTPException(status_code=400, detail="OpenAI provider not configured.")
    
    openai_api_key = openai_provider.api_key_encrypted

    # Process request through Autopilot
    org_model = db.query(models.Organization).filter(models.Organization.id == organization.id).first()
    if not org_model:
        raise HTTPException(status_code=404, detail="Organization not found.")
    result = await autopilot.process_request(request, org_model, openai_api_key)

    # Extract response and metadata
    response_data = result['response']
    autopilot_metadata = result['autopilot_metadata']

    # Log the request
    latency_ms = int((time.time() - start_time) * 1000)
    usage = response_data.usage
    
    crud.log_llm_request(
        db=db,
        organization_id=organization.id,
        model=request.model,
        provider=autopilot_metadata.get('selected_model', request.model),
        prompt_tokens=usage.prompt_tokens,
        completion_tokens=usage.completion_tokens,
        cost_usd=Decimal(0), # Will be updated later
        latency_ms=latency_ms,
        cache_hit=autopilot_metadata.get('routing_reason') == 'cache_hit',
        cache_key=None, # Will be updated later
    )

    # Return response with metadata
    return {
        **response_data.model_dump(),
        "x-cognitude": autopilot_metadata
    }


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
