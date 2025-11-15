"""
Smart routing API endpoint for automatic model selection.
"""
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from .. import schemas
from ..database import get_db
from ..security import get_organization_from_api_key
from ..services.smart_router import SmartRouter
from ..services.router import ProviderRouter


router = APIRouter(tags=["smart-routing"])


class SmartCompletionRequest(BaseModel):
    """Request for smart routing endpoint."""
    messages: List[schemas.Message]
    optimize_for: str = Field(
        default="cost",
        description="Optimization goal: 'cost', 'latency', or 'quality'"
    )
    max_latency_ms: Optional[int] = Field(
        default=None,
        description="Maximum acceptable latency in milliseconds"
    )
    temperature: Optional[float] = Field(default=None, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(default=None, ge=1)
    top_p: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    frequency_penalty: Optional[float] = Field(default=None, ge=-2.0, le=2.0)
    presence_penalty: Optional[float] = Field(default=None, ge=-2.0, le=2.0)
    stop: Optional[List[str]] = None
    n: Optional[int] = Field(default=None, ge=1)


@router.post("/v1/smart/completions", response_model=schemas.ChatCompletionResponse)
async def smart_completions(
    request: SmartCompletionRequest,
    db: Session = Depends(get_db),
    organization: schemas.Organization = Depends(get_organization_from_api_key)
):
    """
    Smart routing endpoint that automatically selects the optimal model.
    
    This endpoint analyzes your prompt complexity and selects the best model
    based on your optimization goal (cost/latency/quality).
    
    **Expected Savings**: 30-50% compared to always using flagship models
    
    **How it works**:
    1. Analyzes prompt complexity (simple/medium/complex)
    2. Filters models suitable for that complexity
    3. Selects optimal model based on your goal
    4. Routes request through standard proxy endpoint
    
    **Examples**:
    
    Simple task (classification):
    ```python
    # Auto-selects gpt-3.5-turbo or claude-haiku
    response = client.chat.completions.create(
        model="smart",  # Special model name
        messages=[{"role": "user", "content": "Classify: positive or negative? 'I love this!'"}]
    )
    ```
    
    Complex task (analysis):
    ```python
    # Auto-selects gpt-4 or claude-opus
    response = client.chat.completions.create(
        model="smart",
        messages=[{"role": "user", "content": "Analyze the economic implications..."}]
    )
    ```
    
    Optimize for latency:
    ```python
    # POST to /v1/smart/completions
    {
        "messages": [...],
        "optimize_for": "latency",  # or "cost", "quality"
        "max_latency_ms": 500
    }
    ```
    """
    # Convert messages to dict format
    messages_dict = [{"role": msg.role, "content": msg.content} for msg in request.messages]
    
    # Classify complexity
    complexity = SmartRouter.classify_complexity(messages_dict)
    
    # Get available providers for this organization
    provider_router = ProviderRouter(db, organization.id)
    providers = provider_router.get_providers(enabled_only=True)
    available_providers = [str(p.provider) for p in providers]
    
    if not available_providers:
        raise HTTPException(
            status_code=400,
            detail="No providers configured. Please configure at least one provider first."
        )
    
    # Get available models from those providers
    available_models = []
    for provider in providers:
        provider_name = str(provider.provider)
        if provider_name == "openai":
            available_models.extend(["gpt-4", "gpt-4-turbo", "gpt-3.5-turbo"])
        elif provider_name == "anthropic":
            available_models.extend(["claude-3-opus", "claude-3-sonnet", "claude-3-haiku"])
        elif provider_name == "groq":
            available_models.extend(["llama3-70b", "mixtral-8x7b"])
        elif provider_name == "google":
            available_models.extend(["gemini-2.5-pro", "gemini-2.5-flash-lite"])
    
    # Select optimal model
    routing_decision = SmartRouter.select_model(
        complexity=complexity,
        optimize_for=request.optimize_for,
        max_latency_ms=request.max_latency_ms,
        available_models=available_models,
        available_providers=available_providers
    )
    
    selected_model = routing_decision["selected_model"]
    
    # Create standard completion request with selected model
    from ..api.proxy import chat_completions
    
    standard_request = schemas.ChatCompletionRequest(
        model=selected_model,
        messages=request.messages,
        temperature=request.temperature,
        max_tokens=request.max_tokens,
        top_p=request.top_p,
        frequency_penalty=request.frequency_penalty,
        presence_penalty=request.presence_penalty
    )
    
    # Call standard proxy endpoint
    response = await chat_completions(
        request_body=standard_request,
        db=db,
        organization=organization
    )
    
    # Add smart routing metadata
    response["smart_routing"] = {
        "complexity": complexity,
        "selected_model": selected_model,
        "selected_provider": routing_decision["selected_provider"],
        "optimize_for": request.optimize_for,
        "estimated_savings_usd": routing_decision.get("estimated_savings_usd", 0),
        "explanation": SmartRouter.explain_selection(routing_decision),
        "alternatives": routing_decision.get("alternatives", [])
    }
    
    return response


@router.post("/v1/smart/analyze")
async def analyze_prompt(
    messages: List[schemas.Message],
    optimize_for: str = "cost",
    db: Session = Depends(get_db),
    organization: schemas.Organization = Depends(get_organization_from_api_key)
):
    """
    Analyze a prompt and get routing recommendations without making the actual call.
    
    Useful for:
    - Understanding which model would be selected
    - Estimating costs before making the call
    - Comparing different optimization strategies
    
    **Example**:
    ```python
    # Analyze what model would be used
    POST /v1/smart/analyze
    {
        "messages": [
            {"role": "user", "content": "Classify this sentiment: I love it!"}
        ],
        "optimize_for": "cost"
    }
    
    # Response:
    {
        "complexity": "simple",
        "selected_model": "gpt-3.5-turbo",
        "estimated_cost": 0.0005,
        "estimated_savings": 0.0295,
        "alternatives": [...]
    }
    ```
    """
    # Convert messages to dict format
    messages_dict = [{"role": msg.role, "content": msg.content} for msg in messages]
    
    # Classify complexity
    complexity = SmartRouter.classify_complexity(messages_dict)
    
    # Get available providers
    provider_router = ProviderRouter(db, organization.id)
    providers = provider_router.get_providers(enabled_only=True)
    available_providers = [str(p.provider) for p in providers]
    
    if not available_providers:
        raise HTTPException(
            status_code=400,
            detail="No providers configured. Please configure at least one provider first."
        )
    
    # Get available models
    available_models = []
    for provider in providers:
        provider_name = str(provider.provider)
        if provider_name == "openai":
            available_models.extend(["gpt-4", "gpt-4-turbo", "gpt-3.5-turbo"])
        elif provider_name == "anthropic":
            available_models.extend(["claude-3-opus", "claude-3-sonnet", "claude-3-haiku"])
        elif provider_name == "groq":
            available_models.extend(["llama3-70b", "mixtral-8x7b"])
        elif provider_name == "google":
            available_models.extend(["gemini-2.5-pro", "gemini-2.5-flash-lite"])
    
    # Debug logging
    print(f"DEBUG: Complexity: {complexity}")
    print(f"DEBUG: Available providers: {available_providers}")
    print(f"DEBUG: Available models: {available_models}")
    print(f"DEBUG: Number of providers: {len(providers)}")
    for p in providers:
        print(f"DEBUG:   Provider: {p.provider}, ID: {p.id}, Enabled: {p.enabled}")
    
    # Get routing decision
    routing_decision = SmartRouter.select_model(
        complexity=complexity,
        optimize_for=optimize_for,
        available_models=available_models,
        available_providers=available_providers
    )
    
    print(f"DEBUG: Routing decision: {routing_decision}")
    
    # Add explanation
    routing_decision["explanation"] = SmartRouter.explain_selection(routing_decision)
    
    return routing_decision


@router.get("/v1/smart/info")
async def smart_routing_info():
    """
    Get information about smart routing capabilities.
    
    Returns:
    - Available optimization modes
    - Complexity classification rules
    - Model characteristics
    """
    return {
        "description": "Smart routing automatically selects the optimal model based on task complexity",
        "optimization_modes": [
            {
                "name": "cost",
                "description": "Minimize cost per request (30-50% savings)"
            },
            {
                "name": "latency",
                "description": "Minimize response time (2-5x faster)"
            },
            {
                "name": "quality",
                "description": "Maximize output quality"
            }
        ],
        "complexity_levels": [
            {
                "name": "simple",
                "description": "Classification, extraction, formatting tasks",
                "example": "Classify sentiment: positive or negative?",
                "recommended_models": ["gpt-3.5-turbo", "claude-3-haiku", "mixtral-8x7b"]
            },
            {
                "name": "medium",
                "description": "Summarization, translation, basic reasoning",
                "example": "Summarize this article in 3 paragraphs",
                "recommended_models": ["gpt-3.5-turbo", "claude-3-sonnet", "llama3-70b"]
            },
            {
                "name": "complex",
                "description": "Analysis, creative writing, advanced reasoning",
                "example": "Analyze the economic implications of this policy",
                "recommended_models": ["gpt-4", "gpt-4-turbo", "claude-3-opus"]
            }
        ],
        "expected_savings": "30-50% compared to always using flagship models",
        "usage": {
            "smart_completions": "POST /v1/smart/completions - Make a request with automatic model selection",
            "analyze": "POST /v1/smart/analyze - Analyze prompt without making the call",
            "info": "GET /v1/smart/info - Get this information"
        }
    }
