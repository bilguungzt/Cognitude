"""
Core LLM proxy with caching and multi-provider routing.
"""
import time
import json
import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Request, Header
from sqlalchemy.orm import Session

from .. import crud, models, schemas
from ..database import get_db
from ..security import get_organization_from_api_key
from ..services.router import ProviderRouter
from ..services.cache_service import cache_service
from ..core.autopilot import AutopilotEngine
from ..core.schema_enforcer import SchemaEnforcer
from ..config import get_settings
from ..limiter import limiter

logger = logging.getLogger(__name__)

router = APIRouter()

settings = get_settings()


@router.post("/v1/chat/completions")
@limiter.limit("100/minute")
async def proxy_chat_completion(
    request: Request,
    db: Session = Depends(get_db),
    organization: models.Organization = Depends(get_organization_from_api_key),
    x_cognitude_schema: Optional[str] = Header(None)
):
    """
    Main proxy endpoint for chat completions with:
    - Intelligent provider routing
    - Response caching
    - Schema enforcement
    - Cost tracking
    - Rate limiting
    """
    start_time = time.time()
    
    try:
        # Parse request body
        body = await request.json()
        request_body = schemas.ChatCompletionRequest(**body)
        
        # Get the actual integer value of organization.id using a scalar query
        org_id_result = db.query(models.Organization.id).filter(
            models.Organization.id == organization.id
        ).first()
        
        if org_id_result:
            org_id = org_id_result[0]
        else:
            raise HTTPException(status_code=404, detail="Organization not found")
        
        # Initialize services
        provider_router = ProviderRouter(db, org_id)
        autopilot = AutopilotEngine(db, cache_service, provider_router)
        schema_enforcer = SchemaEnforcer(db, llm_provider=provider_router)
        
        # Check for schema enforcement
        schema = None
        if x_cognitude_schema:
            try:
                schema = json.loads(x_cognitude_schema)
                # Validate user schema for security/correctness
                from jsonschema import Draft7Validator
                Draft7Validator.check_schema(schema)
            except json.JSONDecodeError:
                raise HTTPException(status_code=400, detail="Invalid JSON in x-cognitude-schema header")
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Schema validation error: {str(e)}")
        
        # Get provider for the request
        provider = provider_router.select_provider(request_body.model)
        if not provider:
            raise HTTPException(status_code=400, detail=f"No provider configured for model: {request_body.model}")
        
        # Route to provider via autopilot
        result = await autopilot.process_request(
            request=request_body,
            organization=organization,
            provider=provider
        )
        
        response_data = result["response"]
        autopilot_metadata = result["autopilot_metadata"]
        
        # Apply schema enforcement if schema was provided
        if schema:
            max_retries = 3
            current_response = response_data if isinstance(response_data, dict) else response_data.model_dump()
            
            for attempt in range(max_retries):
                is_valid, error_msg = schema_enforcer._validate_json_schema(current_response, schema)
                
                if is_valid:
                    response_data = current_response
                    autopilot_metadata["schema_validation"] = {"status": "passed", "attempts": attempt + 1}
                    break
                else:
                    # Log validation failure
                    schema_enforcer._log_validation(
                        project_id=org_id,
                        schema=schema,
                        request=request_body.model_dump(),
                        response=current_response,
                        is_valid=False,
                        error=error_msg,
                        attempt=attempt
                    )
                    
                    # Create retry request
                    retry_request = request_body.model_copy()
                    retry_prompt = schema_enforcer._generate_retry_prompt(schema, error_msg)
                    retry_request.messages.append(
                        schemas.ChatMessage(role="user", content=retry_prompt)
                    )
                    
                    # Get provider for the retry
                    retry_provider = provider_router.select_provider(retry_request.model)
                    if not retry_provider:
                        raise HTTPException(status_code=400, detail=f"No provider configured for model: {retry_request.model}")
                    
                    # Call LLM again via autopilot
                    retry_result = await autopilot.process_request(
                        request=retry_request,
                        organization=organization,
                        provider=retry_provider
                    )
                    current_response = retry_result["response"]
                    if isinstance(current_response, dict):
                        current_response = current_response
                    else:
                        current_response = current_response.model_dump()
                    
                    # On final attempt, use response even if invalid
                    if attempt == max_retries - 1:
                        response_data = current_response
                        autopilot_metadata["schema_validation"] = {
                            "status": "failed_after_retries",
                            "attempts": attempt + 1,
                            "error": error_msg
                        }
        else:
            if isinstance(response_data, dict):
                response_data = response_data
            else:
                response_data = response_data.model_dump()
        
        # Calculate costs and update response
        provider_info = autopilot_metadata.get("provider_info", {})
        cost = provider_info.get("cost", 0.0)
        cache_hit = bool(autopilot_metadata.get("cache_key"))
        
        # Add cognitude metadata
        response_data["x-cognitude"] = {
            "cached": False,
            "hit": False,
            "cost": float(cost),
            "provider": provider_info.get("name", "unknown"),
            "cache_key": autopilot_metadata.get("cache_key"),
            "routing_metadata": autopilot_metadata
        }
        
        # Cache the response if caching is enabled and this was not a cache hit
        if getattr(settings, 'CACHE_ENABLED', False) and not cache_hit:
            cache_key = cache_service.set_response(
                db=db,
                organization_id=org_id,
                request=request_body,
                response_data=response_data,
                model=autopilot_metadata.get("selected_model", request_body.model),
                provider=provider_info.get("name", "unknown"),
                prompt_tokens=response_data.get("usage", {}).get("prompt_tokens", 0),
                completion_tokens=response_data.get("usage", {}).get("completion_tokens", 0),
                cost_usd=cost,
                model_override=autopilot_metadata.get("selected_model"),
            )
            response_data["x-cognitude"]["cache_key"] = cache_key
        
        # Log the request
        crud.log_llm_request(
            db=db,
            organization_id=org_id,
            model=request_body.model,
            provider=provider_info.get("name", "unknown"),
            prompt_tokens=response_data.get("usage", {}).get("prompt_tokens", 0),
            completion_tokens=response_data.get("usage", {}).get("completion_tokens", 0),
            cost_usd=cost,
            latency_ms=int((time.time() - start_time) * 1000),
            cache_hit=cache_hit
        )
        
        return response_data
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        # Log the full error with stack trace
        logger.error(f"Proxy error: {e}", exc_info=True)
        # Return more detailed error in development, generic in production
        error_detail = f"Internal proxy error: {str(e)}" if settings.ENVIRONMENT != "production" else "Internal proxy error"
        raise HTTPException(status_code=500, detail=error_detail)


@router.get("/v1/models")
async def list_models(
    db: Session = Depends(get_db),
    organization: models.Organization = Depends(get_organization_from_api_key)
):
    """List available models from configured providers."""
    # Get the actual integer value of organization.id
    org_id_result = db.query(models.Organization.id).filter(
        models.Organization.id == organization.id
    ).first()
    
    if org_id_result:
        org_id = org_id_result[0]
    else:
        raise HTTPException(status_code=404, detail="Organization not found")
    
    provider_router = ProviderRouter(db, org_id)
    providers = provider_router.get_providers(enabled_only=True)
    
    models_list = []
    for provider in providers:
        # Add models based on provider type
        if str(provider.provider) == "openai":
            models_list.extend([
                # Latest Models (2025)
                {"id": "gpt-5.1", "object": "model", "owned_by": "openai"},
                {"id": "gpt-5.1-instant", "object": "model", "owned_by": "openai"},
                {"id": "gpt-5.1-thinking", "object": "model", "owned_by": "openai"},
                {"id": "gpt-5", "object": "model", "owned_by": "openai"},
                {"id": "gpt-4.5", "object": "model", "owned_by": "openai"},
                {"id": "gpt-4.1", "object": "model", "owned_by": "openai"},
                {"id": "o4-mini", "object": "model", "owned_by": "openai"},
                # Existing Models
                {"id": "o1-preview", "object": "model", "owned_by": "openai"},
                {"id": "o1-mini", "object": "model", "owned_by": "openai"},
                {"id": "gpt-4-turbo", "object": "model", "owned_by": "openai"},
                {"id": "gpt-4o", "object": "model", "owned_by": "openai"},
                {"id": "gpt-4o-mini", "object": "model", "owned_by": "openai"},
                {"id": "gpt-4", "object": "model", "owned_by": "openai"},
            ])
        elif str(provider.provider) == "anthropic":
            models_list.extend([
                # Latest Models (2025)
                {"id": "claude-sonnet-4.5", "object": "model", "owned_by": "anthropic"},
                {"id": "claude-haiku-4.5", "object": "model", "owned_by": "anthropic"},
                {"id": "claude-opus-4.1", "object": "model", "owned_by": "anthropic"},
                # Existing Models
                {"id": "claude-3-5-sonnet-20241022", "object": "model", "owned_by": "anthropic"},
                {"id": "claude-3-5-sonnet-20240620", "object": "model", "owned_by": "anthropic"},
                {"id": "claude-3-opus-20240229", "object": "model", "owned_by": "anthropic"},
                {"id": "claude-3-sonnet-20240229", "object": "model", "owned_by": "anthropic"},
                {"id": "claude-3-haiku-20240307", "object": "model", "owned_by": "anthropic"},
            ])
        elif str(provider.provider) == "google":
            models_list.extend([
                # Latest Models (2025)
                {"id": "gemini-2.5-pro", "object": "model", "owned_by": "google"},
                {"id": "gemini-2.5-pro-deep-think", "object": "model", "owned_by": "google"},
                {"id": "gemini-2.0-flash-exp", "object": "model", "owned_by": "google"},
                {"id": "gemini-1.5-pro", "object": "model", "owned_by": "google"},
                {"id": "gemini-1.5-flash", "object": "model", "owned_by": "google"},
                {"id": "gemini-pro", "object": "model", "owned_by": "google"},
                {"id": "gemini-flash", "object": "model", "owned_by": "google"},
            ])
        elif str(provider.provider) == "groq":
            models_list.extend([
                # Latest Models (2025)
                {"id": "groq-4", "object": "model", "owned_by": "groq"},
                {"id": "fast-1", "object": "model", "owned_by": "groq"},
                # Llama 4 (2025)
                {"id": "llama-4-scout", "object": "model", "owned_by": "meta"},
                {"id": "llama-4-maverick", "object": "model", "owned_by": "meta"},
                # Existing Models
                {"id": "llama-3.3-70b-versatile", "object": "model", "owned_by": "groq"},
                {"id": "llama-3.1-70b-versatile", "object": "model", "owned_by": "groq"},
                {"id": "mixtral-8x7b-32768", "object": "model", "owned_by": "groq"},
                {"id": "gemma-7b-it", "object": "model", "owned_by": "groq"},
            ])
    
    return {"object": "list", "data": models_list}
