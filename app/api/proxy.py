"""
Core LLM proxy endpoint with caching and multi-provider routing.
"""
import time
from typing import Optional
import json
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, Response, Header, Request
from sqlalchemy.orm import Session

from .. import crud, schemas, models
from ..database import get_db
from ..security import get_organization_from_api_key
from ..services.router import ProviderRouter
from ..services.tokens import count_messages_tokens
from ..services.pricing import calculate_cost
from ..services.redis_cache import redis_cache
from ..core.autopilot import AutopilotEngine
from ..core.schema_enforcer import SchemaEnforcer, validate_user_schema
from ..limiter import limiter


router = APIRouter(tags=["proxy"])


@router.post("/v1/chat/completions",
             response_model=schemas.ChatCompletionResponse,
             responses={
                 200: {
                     "description": "Successful response",
                     "content": {
                         "application/json": {
                             "example": {
                                 "id": "chatcmpl-abc123",
                                 "object": "chat.completion",
                                 "created": 170490240,
                                 "model": "gpt-3.5-turbo",
                                 "choices": [
                                     {
                                         "index": 0,
                                         "message": {
                                             "role": "assistant",
                                             "content": "Hello! How can I help you today?"
                                         },
                                         "finish_reason": "stop"
                                     }
                                 ],
                                 "usage": {
                                     "prompt_tokens": 10,
                                     "completion_tokens": 12,
                                     "total_tokens": 22
                                 },
                                 "x-cognitude": {
                                     "cached": False,
                                     "cost": 0.0024,
                                     "provider": "openai",
                                     "cache_key": "chat:gpt-3.5-turbo:hash123"
                                 }
                             }
                         }
                     }
                 },
                 401: {
                     "description": "Invalid or missing API key",
                     "content": {
                         "application/json": {
                             "example": {
                                 "error": {
                                     "message": "Invalid or missing API Key",
                                     "type": "authentication_error",
                                     "code": "INVALID_API_KEY"
                                 }
                             }
                         }
                     }
                 },
                 429: {
                     "description": "Rate limit exceeded",
                     "content": {
                         "application/json": {
                             "example": {
                                 "error": {
                                     "message": "Rate limit exceeded",
                                     "type": "rate_limit_error",
                                     "code": "RATE_LIMIT_EXCEEDED",
                                     "retry_after": 60
                                 }
                             }
                         }
                     }
                 },
                 500: {
                     "description": "Internal server error",
                     "content": {
                         "application/json": {
                             "example": {
                                 "error": {
                                     "message": "Internal server error",
                                     "type": "api_error",
                                     "code": "INTERNAL_ERROR"
                                 }
                             }
                         }
                     }
                 }
             })
@limiter.limit("100/minute")
async def chat_completions(
    request_body: schemas.ChatCompletionRequest,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    organization: schemas.Organization = Depends(get_organization_from_api_key),
    x_cognitude_schema: Optional[str] = Header(None)
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
    
    # Add request size limit check (10MB max)
    content_length = request.headers.get("content-length")
    if content_length:
        try:
            content_length_int = int(content_length)
            if content_length_int > 10 * 1024 * 1024:  # 10MB limit
                raise HTTPException(
                    status_code=413,
                    detail="Request size exceeds maximum allowed limit of 10MB"
                )
        except ValueError:
            # If content-length header is invalid, continue processing
            pass
    
    # Instantiate Autopilot Engine
    autopilot = AutopilotEngine(db, redis_cache)

    # Get OpenAI API key
    provider_router = ProviderRouter(db, organization.id)
    openai_provider = provider_router.select_provider("gpt-4")
    if not openai_provider:
        raise HTTPException(status_code=400, detail="OpenAI provider not configured.")
    
    openai_api_key = openai_provider.get_api_key() if openai_provider else None
    if not openai_api_key:
        raise HTTPException(status_code=400, detail="Provider API key not configured. Please configure your provider credentials.")

    # Process request through Autopilot
    org_model = db.query(models.Organization).filter(models.Organization.id == organization.id).first()
    if not org_model:
        raise HTTPException(status_code=404, detail="Organization not found.")
    
    # Validate organization has rate limit configuration
    rate_limit_config = db.query(models.RateLimitConfig).filter(
        models.RateLimitConfig.organization_id == organization.id
    ).first()
    
    if not rate_limit_config:
        # Create default rate limit config if none exists
        rate_limit_config = models.RateLimitConfig(
            organization_id=organization.id,
            requests_per_minute=100,
            requests_per_hour=3000,
            requests_per_day=50000
        )
        db.add(rate_limit_config)
        db.commit()

    # 1. Schema Enforcement Setup
    schema = None
    if x_cognitude_schema:
        try:
            schema = json.loads(x_cognitude_schema)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid JSON in x-cognitude-schema header")
        
        try:
            validate_user_schema(schema)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=f"Schema validation failed: {e}")

    # The AutopilotEngine will act as the LLM provider for retries
    schema_enforcer = SchemaEnforcer(db=db, llm_provider=autopilot)

    # 2. Inject schema prompt if schema is provided
    if schema:
        request_dict = request_body.model_dump()
        modified_request_dict = schema_enforcer.enforce_schema(
            request=request_dict,
            schema=schema
        )
        request_body = schemas.ChatCompletionRequest(**modified_request_dict)

    # 3. Call LLM via Autopilot
    result = await autopilot.process_request(request_body, org_model, openai_api_key)
    response_data = result['response']
    autopilot_metadata = result['autopilot_metadata']

    # Log the initial request before validation
    latency_ms = int((time.time() - start_time) * 1000)
    usage = response_data.usage
    
    # Calculate the cost before logging
    model_name = autopilot_metadata.get('selected_model', request_body.model)
    cost = calculate_cost(usage.prompt_tokens, usage.completion_tokens, model_name) or Decimal(0)

    llm_request_log = crud.log_llm_request(
        db=db,
        organization_id=organization.id,
        model=request_body.model,
        provider=autopilot_metadata.get('selected_model', request_body.model),
        prompt_tokens=usage.prompt_tokens,
        completion_tokens=usage.completion_tokens,
        cost_usd=cost,
        latency_ms=latency_ms,
        cache_hit=autopilot_metadata.get('routing_reason') == 'cache_hit',
        cache_key=None, # Placeholder
    )
    db.flush() # Ensure llm_request_log gets an ID

    # 4. Validate and Retry if schema was provided
    if schema:
        # Perform schema validation and retries within the proxy endpoint
        # instead of in the schema enforcer to avoid circular dependency
        max_retries = 3
        current_response = response_data.model_dump()
        
        for attempt in range(max_retries):
            is_valid, error_message = schema_enforcer._validate_json_schema(current_response, schema)
            
            if is_valid:
                response_data = schemas.ChatCompletionResponse(**current_response)
                autopilot_metadata['x_cognitude_validation'] = {"status": "completed", "attempts": attempt + 1}
                break
            else:
                # Log the validation failure
                schema_enforcer._log_validation(organization.id, request_body.model_dump(), current_response, False, error_message, attempt)
                
                # Create a new request with retry instructions
                retry_prompt = schema_enforcer._generate_retry_prompt(schema, error_message)
                new_request = request_body.model_copy()
                new_request.messages.append(schemas.ChatMessage(role="user", content=retry_prompt))
                
                # Call the LLM again via autopilot
                result = await autopilot.process_request(new_request, org_model, openai_api_key)
                current_response = result['response'].model_dump()
                
                # If this was the last attempt, use the final response even if invalid
                if attempt == max_retries - 1:
                    response_data = schemas.ChatCompletionResponse(**current_response)
                    autopilot_metadata['x_cognitude_validation'] = {"status": "failed", "attempts": attempt + 1, "error": error_message}

    # 5. Return final response
    final_response_dict = response_data.model_dump()
    final_response_dict["x-cognitude"] = autopilot_metadata
    
    return final_response_dict
@router.get("/v1/models",
             responses={
                 200: {
                     "description": "List of available models",
                     "content": {
                         "application/json": {
                             "example": {
                                 "object": "list",
                                 "data": [
                                     {
                                         "id": "gpt-4",
                                         "object": "model",
                                         "owned_by": "openai"
                                     },
                                     {
                                         "id": "claude-3-opus",
                                         "object": "model",
                                         "owned_by": "anthropic"
                                     }
                                 ]
                             }
                         }
                     }
                 },
                 401: {
                     "description": "Invalid or missing API key",
                     "content": {
                         "application/json": {
                             "example": {
                                 "error": {
                                     "message": "Invalid or missing API Key",
                                     "type": "authentication_error",
                                     "code": "INVALID_API_KEY"
                                 }
                             }
                         }
                     }
                 },
                 500: {
                     "description": "Internal server error",
                     "content": {
                         "application/json": {
                             "example": {
                                 "error": {
                                     "message": "Internal server error",
                                     "type": "api_error",
                                     "code": "INTERNAL_ERROR"
                                 }
                             }
                         }
                     }
                 }
             })
async def list_models(
    db: Session = Depends(get_db),
    organization: schemas.Organization = Depends(get_organization_from_api_key)
):

    """
    List available models based on configured providers.
    OpenAI-compatible endpoint.
    
    ## Authentication
    This endpoint requires API key authentication. You can authenticate using:
    - `X-API-Key: your-api-key` header
    - `Authorization: Bearer your-api-key` header (OpenAI-compatible format)
    
    **Example:**
    ```bash
    curl https://api.cognitude.io/v1/models \\
      -H "Authorization: Bearer cog_abc123def456..."
    ```
    
    ## Response
    Returns a list of available models based on your configured providers.
    Each model includes:
    - `id`: Model identifier (e.g., "gpt-4", "claude-3-opus")
    - `object`: Always "model"
    - `owned_by`: Provider name (e.g., "openai", "anthropic")
    
    ## Error Responses
    Common error codes:
    - `401`: Invalid or missing API key
    - `403`: Insufficient permissions
    - `500`: Internal server error
    """
    provider_router = ProviderRouter(db, organization.id)
    providers = provider_router.get_providers(enabled_only=True)
    
    # Build list of available models based on providers
    models_list = []
    
    for provider_config in providers:
        if str(provider_config.provider) == "openai":
            models_list.extend([
                {"id": "gpt-4", "object": "model", "owned_by": "openai"},
                {"id": "gpt-4-turbo", "object": "model", "owned_by": "openai"},
                {"id": "gpt-3.5-turbo", "object": "model", "owned_by": "openai"},
            ])
        elif str(provider_config.provider) == "anthropic":
            models_list.extend([
                {"id": "claude-3-opus", "object": "model", "owned_by": "anthropic"},
                {"id": "claude-3-sonnet", "object": "model", "owned_by": "anthropic"},
                {"id": "claude-3-haiku", "object": "model", "owned_by": "anthropic"},
            ])
        elif str(provider_config.provider) == "mistral":
            models_list.extend([
                {"id": "mistral-large", "object": "model", "owned_by": "mistral"},
                {"id": "mistral-medium", "object": "model", "owned_by": "mistral"},
            ])
        elif str(provider_config.provider) == "groq":
            models_list.extend([
                {"id": "llama3-70b", "object": "model", "owned_by": "groq"},
                {"id": "mixtral-8x7b", "object": "model", "owned_by": "groq"},
            ])
    
    return {
        "object": "list",
        "data": models_list
    }
