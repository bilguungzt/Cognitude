from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import StreamingResponse
import httpx
import time
import os
from sqlalchemy.orm import Session

from .. import crud, models
from ..database import SessionLocal
from ..security import verify_api_key, get_organization_from_api_key
from ..schemas import ChatCompletionRequest, ChatCompletionResponse
from typing import Generator


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

router = APIRouter()

# Cost calculation constants (dummy rates for now)
COST_PER_M_TOKEN_INPUT = 0.03  # $0.03 per 1k tokens for input
COST_PER_M_TOKEN_OUTPUT = 0.06  # $0.06 per 1k tokens for output


def calculate_cost(model: str, prompt_tokens: int, completion_tokens: int) -> float:
    """
    Calculate the cost of an API call based on token usage.
    Using dummy rates for now - in a real implementation, you would have
    different rates for different models.
    """
    input_cost = (prompt_tokens / 1_000_000) * COST_PER_M_TOKEN_INPUT
    output_cost = (completion_tokens / 1_000) * COST_PER_M_TOKEN_OUTPUT
    return input_cost + output_cost


@router.post(
    "/v1/chat/completions",
    summary="OpenAI Chat Completions Proxy",
    description="""
## Drop-in replacement for OpenAI's chat completions API

This endpoint acts as a transparent proxy while logging all usage metrics for cost tracking and analytics.

### 🔄 How it works:

1. **User makes request** with two API keys:
   - `Authorization: Bearer <openai-key>` - Your OpenAI API key (passed through to OpenAI)
   - `X-API-Key: <driftassure-key>` - Your DriftAssure API key (for authentication & logging)

2. **DriftAssure logs everything** to database:
   - Request timestamp
   - Model used (gpt-4, gpt-3.5-turbo, etc.)
   - Token usage (prompt + completion)
   - Cost calculated based on model pricing
   - Response latency in milliseconds
   - Organization ID (from your X-API-Key)

3. **Request forwarded** to OpenAI API with your OpenAI key

4. **Response returned** with full OpenAI response format

### 💰 Cost Tracking

- Automatically calculates cost based on token usage
- Costs visible in `/analytics/usage` endpoint
- Real-time tracking for all requests
- No markup - just transparent logging

### 🔐 Privacy & Security

**What gets logged:**
- ✅ Model name
- ✅ Prompt tokens used
- ✅ Completion tokens used
- ✅ Total cost (calculated)
- ✅ Response latency (ms)

**What does NOT get logged:**
- ❌ Message content (never logged for privacy)
- ❌ User data or identifiable information
- ❌ API keys (never stored)

### 📝 Example Usage (Python):

```python
from openai import OpenAI

client = OpenAI(
    api_key="your-openai-key",
    base_url="https://api.driftassure.com",
    default_headers={"X-API-Key": "your-driftassure-key"}
)

response = client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "Hello!"}]
)
```

### 🔗 Integration with Analytics

All logged data is available via the `/analytics/usage` endpoint:
- View total requests and costs
- Track usage trends over time
- Monitor API performance
- Calculate cost savings
    """,
    tags=["proxy"],
    response_model=ChatCompletionResponse,
    responses={
        200: {
            "description": "Successful OpenAI API response",
            "content": {
                "application/json": {
                    "example": {
                        "id": "chatcmpl-123",
                        "object": "chat.completion",
                        "created": 1699492800,
                        "model": "gpt-3.5-turbo",
                        "usage": {
                            "prompt_tokens": 10,
                            "completion_tokens": 20,
                            "total_tokens": 30
                        },
                        "choices": [
                            {
                                "index": 0,
                                "message": {
                                    "role": "assistant",
                                    "content": "Hello! How can I help you today?"
                                },
                                "finish_reason": "stop"
                            }
                        ]
                    }
                }
            }
        },
        401: {
            "description": "Invalid or missing X-API-Key",
            "content": {
                "application/json": {
                    "example": {"detail": "Invalid API key"}
                }
            }
        },
        502: {
            "description": "Error connecting to OpenAI API",
            "content": {
                "application/json": {
                    "example": {"detail": "Error connecting to OpenAI API: Connection timeout"}
                }
            }
        }
    }
)
async def proxy_chat_completions(
    request: Request,
    organization=Depends(get_organization_from_api_key),
    db: Session = Depends(get_db)
):
    """
    Proxy endpoint for OpenAI's chat completions API.
    This endpoint forwards requests to OpenAI and logs usage metrics.
    """
    # Get the request body
    body = await request.json()
    
    # Start timing for latency measurement
    start_time = time.time()
    
    # Get OpenAI API key from environment
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="OpenAI API key not configured on the server"
        )
    
    # Forward the request to OpenAI
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                json=body,
                headers={
                    "Authorization": f"Bearer {openai_api_key}",
                    "Content-Type": "application/json"
                },
                timeout=60.0  # 60 second timeout
            )
            
            # Calculate latency in milliseconds
            latency_ms = (time.time() - start_time) * 1000
            
            # Process the response
            response_data = response.json()
            
            # Extract token usage from OpenAI response
            prompt_tokens = 0
            completion_tokens = 0
            total_tokens = 0
            
            if "usage" in response_data:
                usage = response_data["usage"]
                prompt_tokens = usage.get("prompt_tokens", 0)
                completion_tokens = usage.get("completion_tokens", 0)
                total_tokens = usage.get("total_tokens", 0)
            
            # Calculate cost
            model_name = body.get("model", "unknown")
            total_cost = calculate_cost(model_name, prompt_tokens, completion_tokens)
            
            # Create API log entry
            api_log = models.APILog(
                organization_id=organization.id,
                provider="openai",
                model=model_name,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_cost=total_cost,
                latency_ms=latency_ms
            )
            db.add(api_log)
            db.commit()
            
            # Return the OpenAI response to the user
            return response_data
            
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Error connecting to OpenAI API: {str(e)}"
            )
        except httpx.HTTPStatusError as e:
            # If OpenAI returns an error, propagate it to the client
            try:
                error_detail = e.response.json()
            except Exception:
                error_detail = {"error": {"message": f"OpenAI API error: {str(e)}"}}
            
            # Calculate latency even for error responses
            latency_ms = (time.time() - start_time) * 1000
            
            # Log the error request as well
            model_name = body.get("model", "unknown")
            api_log = models.APILog(
                organization_id=organization.id,
                provider="openai",
                model=model_name,
                prompt_tokens=0,  # No tokens used in error case
                completion_tokens=0,
                total_cost=0.0,
                latency_ms=latency_ms
            )
            db.add(api_log)
            db.commit()
            
            raise HTTPException(
                status_code=e.response.status_code,
                detail=error_detail
            )
