# API Documentation Improvements Needed

## Current Issues

Your Swagger/ReDoc is missing key information about the OpenAI proxy flow:

### Missing Documentation:

1. **Proxy Endpoint Documentation** (`/v1/chat/completions`)
   - ❌ Missing detailed explanation of the flow
   - ❌ Missing example of how to pass both API keys
   - ❌ Missing explanation of what gets logged
   - ❌ Missing cost calculation details

2. **Analytics Endpoint Documentation** (`/analytics/usage`)
   - ❌ Missing explanation of what metrics are available
   - ❌ Missing examples of response data
   - ❌ Missing explanation of date filtering

## What Should Be Added

### 1. Enhanced Proxy Endpoint Documentation

```python
@router.post(
    "/v1/chat/completions",
    summary="OpenAI Chat Completions Proxy",
    description="""
    ## Drop-in replacement for OpenAI's chat completions API
    
    ### How it works:
    1. **User makes request** with two API keys:
       - `Authorization: Bearer <openai-key>` - Your OpenAI API key  
       - `X-API-Key: <driftassure-key>` - Your DriftAssure API key
    
    2. **DriftAssure logs everything** to database:
       - Request timestamp
       - Model used (gpt-4, gpt-3.5-turbo, etc.)
       - Token usage (prompt + completion)
       - Cost calculated based on model pricing
       - Response latency in milliseconds
       - Organization ID (from your X-API-Key)
    
    3. **Request forwarded** to OpenAI API with your OpenAI key
    
    4. **Response returned** with full OpenAI response format
    
    ### Cost Tracking
    - Automatically calculates cost based on token usage
    - Costs visible in `/analytics/usage` endpoint
    - Real-time tracking for all requests
    
    ### Example Usage (Python):
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
    
    ### What Gets Logged:
    - ✅ Model name
    - ✅ Prompt tokens used
    - ✅ Completion tokens used  
    - ✅ Total cost (calculated)
    - ✅ Response latency (ms)
    - ❌ Message content (never logged for privacy)
    """,
    tags=["proxy"],
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
                        "choices": [...]
                    }
                }
            }
        }
    }
)
```

### 2. Enhanced Analytics Endpoint Documentation

```python
@router.get(
    "/analytics/usage",
    summary="Get Usage Analytics",
    description="""
    ## Retrieve aggregated usage metrics and cost analytics
    
    ### What You Get:
    - **Total requests**: Count of all API calls made
    - **Total cost**: Sum of all costs in USD
    - **Average latency**: Mean response time in milliseconds
    - **Daily breakdown**: Usage and costs per day
    
    ### Use Cases:
    - 📊 Power your dashboard with real-time metrics
    - 💰 Track cost savings vs direct OpenAI usage
    - ⚡ Monitor API performance and latency
    - 📈 Analyze usage trends over time
    
    ### Optional Filters:
    - `start_date`: YYYY-MM-DD format (e.g., 2025-11-01)
    - `end_date`: YYYY-MM-DD format (e.g., 2025-11-09)
    
    ### Example Response:
    ```json
    {
      "total_requests": 15420,
      "total_cost": 127.45,
      "average_latency": 342.5,
      "usage_by_day": [
        {
          "date": "2025-11-09",
          "requests": 1250,
          "cost": 12.30
        }
      ]
    }
    ```
    
    ### Dashboard Integration:
    - Show "Total Saved" by comparing to direct OpenAI pricing
    - Display cache hit rate (if caching enabled)
    - Show cost reduction percentage
    - Visualize daily cost trends
    """,
    tags=["analytics"]
)
```

## Action Items

✅ **Immediate**: Add these docstrings to your endpoints
✅ **Recommended**: Create Pydantic response models for better schema generation
✅ **Optional**: Add more example code snippets in different languages
