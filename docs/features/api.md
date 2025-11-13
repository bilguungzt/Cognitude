# Cognitude LLM Proxy - API Documentation# Cognitude LLM Proxy - API Documentation

**Version:** 1.0.0 **Version:** 1.0.0

**Last Updated:** January 2025**Last Updated:** November 10, 2025

## Overview## Overview

Cognitude is an OpenAI-compatible LLM proxy that provides intelligent caching, multi-provider routing, smart model selection, and comprehensive cost analytics. Drop it in front of your OpenAI SDK calls to get 30-85% cost savings with zero code changes.Cognitude is an OpenAI-compatible LLM proxy that provides intelligent caching, multi-provider routing, smart model selection, and comprehensive cost analytics. Drop it in front of your OpenAI SDK calls to get 30-85% cost savings with zero code changes.

## Base URLs## Base URLs

```

Development: http://localhost:8000Development: http://localhost:8000

Production:  https://your-domain.comProduction:  https://your-domain.com

```

## Key Features## Key Features

- 🔄 **OpenAI Compatible**: Drop-in replacement for OpenAI SDK- 🔄 **OpenAI Compatible**: Drop-in replacement for OpenAI SDK

- 💾 **Intelligent Caching**: 30-70% cost savings via Redis + PostgreSQL - 💾 **Intelligent Caching**: 30-70% cost savings via Redis + PostgreSQL

- 🧠 **Smart Routing**: Auto-select cheapest model for task (30-50% additional savings)- 🧠 **Smart Routing**: Auto-select cheapest model for task (30-50% additional savings)

- 🌐 **Multi-Provider**: OpenAI, Anthropic, Mistral, Groq support- 🌐 **Multi-Provider**: OpenAI, Anthropic, Mistral, Groq support

- 💰 **Cost Tracking**: Per-request cost calculation and analytics- 💰 **Cost Tracking**: Per-request cost calculation and analytics

- 📊 **Analytics**: Usage metrics, recommendations, insights- 📊 **Analytics**: Usage metrics, recommendations, insights

- ⚡ **Rate Limiting**: Protect against abuse (configurable per org)- ⚡ **Rate Limiting**: Protect against abuse (configurable per org)

- 🔔 **Alerts**: Proactive cost/usage notifications (Slack, email, webhook)- 🔔 **Alerts**: Proactive cost/usage notifications (Slack, email, webhook)

---

## Quick Start## Quick Start

### 1. Register Your Organization### 1. Register Your Organization

`bash`bash

curl -X POST http://localhost:8000/auth/register \curl -X POST http://localhost:8000/auth/register \

-H "Content-Type: application/json" \ -H "Content-Type: application/json" \

-d '{"name": "Acme Corp"}' -d '{"name": "Acme Corp"}'

````



**Response:****Response:**

```json```json

{{

  "id": 1,  "id": 1,

  "name": "Acme Corp",  "name": "Acme Corp",

  "api_key": "cog_abc123def456...",  "api_key": "cog_abc123def456...",


}}

````

⚠️ **Save your API key!** It's only shown once.⚠️ **Save your API key!** It's only shown once.

---

### 2. Configure a Provider### 2. Configure a Provider

Add your OpenAI API key (or other provider):Add your OpenAI API key (or other provider):

`bash`bash

curl -X POST http://localhost:8000/providers/ \curl -X POST http://localhost:8000/providers/ \

-H "X-API-Key: cog_abc123def456..." \ -H "X-API-Key: cog_abc123def456..." \

-H "Content-Type: application/json" \ -H "Content-Type: application/json" \

-d '{ -d '{

    "provider": "openai",    "provider": "openai",

    "api_key": "sk-your-openai-key",    "api_key": "sk-your-openai-key",

    "priority": 1,    "priority": 1,

    "enabled": true    "enabled": true

}' }'

````



**Supported Providers:****Supported Providers:**

- `openai` - OpenAI (GPT-4, GPT-3.5, etc.)- `openai` - OpenAI (GPT-4, GPT-3.5, etc.)

- `anthropic` - Anthropic (Claude 3 Opus, Sonnet, Haiku)- `anthropic` - Anthropic (Claude 3 Opus, Sonnet, Haiku)

- `mistral` - Mistral AI- `mistral` - Mistral AI

- `groq` - Groq (fast inference)- `groq` - Groq (fast inference)



------



### 3. Use the LLM Proxy### 3. Use the LLM Proxy



Replace your OpenAI base URL with Cognitude:Replace your OpenAI base URL with Cognitude:



```python```python

from openai import OpenAIfrom openai import OpenAI



# Before: OpenAI directly# Before: OpenAI directly

# client = OpenAI(api_key="sk-openai-key")# client = OpenAI(api_key="sk-openai-key")



# After: Through Cognitude proxy# After: Through Cognitude proxy

client = OpenAI(client = OpenAI(

    api_key="cog_abc123def456...",  # Your Cognitude API key    api_key="cog_abc123def456...",  # Your Cognitude API key

    base_url="http://localhost:8000/v1"  # Point to Cognitude    base_url="http://localhost:8000/v1"  # Point to Cognitude

))



# Same code works!# Same code works!

response = client.chat.completions.create(response = client.chat.completions.create(

    model="gpt-3.5-turbo",    model="gpt-3.5-turbo",

    messages=[{"role": "user", "content": "Hello!"}]    messages=[{"role": "user", "content": "Hello!"}]

))

print(response.choices[0].message.content)print(response.choices[0].message.content)

````

**That's it!** You're now getting:**That's it!** You're now getting:

- ✅ Automatic response caching- ✅ Automatic response caching

- ✅ Cost tracking- ✅ Cost tracking

- ✅ Multi-provider routing- ✅ Multi-provider routing

- ✅ Rate limiting- ✅ Rate limiting

- ✅ Usage analytics- ✅ Usage analytics

---

## Authentication## Authentication

All endpoints (except `/auth/register`) require an API key.All endpoints (except `/auth/register`) require an API key.

### Header-based (Recommended)### Header-based (Recommended)

`bash`bash

curl -H "X-API-Key: cog_abc123..." http://localhost:8000/analytics/usagecurl -H "X-API-Key: cog_abc123..." http://localhost:8000/analytics/usage


---

## API Reference

### 💬 Chat Completions (OpenAI Compatible)


#### POST /v1/chat/completions

OpenAI-compatible chat completions endpoint with automatic caching and cost tracking.

**Headers:**

- `Authorization: Bearer cog_abc123...` (standard OpenAI format)
- OR `X-API-Key: cog_abc123...`

**Request:**
```json
{
  "model": "gpt-3.5-turbo",
  "messages": [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "What is the capital of France?"}
  ],
  "temperature": 0.7,
  "max_tokens": 150
}
```

**Response:**
```json
{
  "id": "chatcmpl-abc123",
  "object": "chat.completion",
  "created": 1704902400,
  "model": "gpt-3.5-turbo",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "The capital of France is Paris."
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 20,
    "completion_tokens": 8,
    "total_tokens": 28
  },
  "x_cognitude": {
    "cached": false,
    "cost": 0.000042,
    "provider": "openai",
    "cache_key": "chat:gpt-3.5-turbo:hash123"
  }
}
```

**Caching Behavior:**
- Identical requests return cached responses instantly (0ms latency)
- Redis cache: 1 hour TTL for fast access
- PostgreSQL cache: Long-term storage for analytics
- Costs $0 when served from cache

**Supported Parameters:**
- `model` (required): Model name (gpt-4, gpt-3.5-turbo, claude-3-opus, etc.)
- `messages` (required): Array of message objects
- `temperature`: 0-2, controls randomness
- `max_tokens`: Maximum tokens to generate
- `top_p`: Nucleus sampling parameter
- `frequency_penalty`: -2 to 2
- `presence_penalty`: -2 to 2
- `stream`: Boolean (streaming not yet supported)

---

### 🧠 Smart Routing

#### POST /v1/smart/completions

Auto-select the cheapest model that can handle the task complexity.

**Headers:**
- `Authorization: Bearer cog_abc123...`

**Request:**
```json
{
  "messages": [
    {"role": "user", "content": "What is 2+2?"}
  ],
  "temperature": 0.7
}
```

**Response:**
```json
{
  "id": "chatcmpl-abc123",
  "model": "gpt-3.5-turbo",
  "choices": [...],
  "usage": {...},
  "x_cognitude": {
    "cached": false,
    "cost": 0.000012,
    "provider": "openai",
    "selected_model": "gpt-3.5-turbo",
    "complexity_score": 0.15,
    "reasoning": "Simple arithmetic, using cheapest model"
  }
}
```

**How it Works:**
- Analyzes prompt complexity (length, keywords, structure)
- Selects cheapest model that can handle the task
- Simple queries → gpt-3.5-turbo (cheap)
- Complex queries → gpt-4 (expensive but needed)
- **Typical savings: 30-50% vs always using GPT-4**

---

### 📊 Analytics

#### GET /analytics/usage

Get usage metrics and cost breakdown.

**Headers:**
- `X-API-Key: cog_abc123...`

**Query Parameters:**
- `start_date`: ISO 8601 date (default: 7 days ago)
- `end_date`: ISO 8601 date (default: now)
- `group_by`: `day` | `model` | `provider` (default: `day`)

**Request:**
```bash
curl "http://localhost:8000/analytics/usage?start_date=2025-01-01&end_date=2025-01-10&group_by=model" \
  -H "X-API-Key: cog_abc123..."
```

**Response:**
```json
{
  "total_requests": 1250,
  "total_cost": 15.42,
  "cache_hits": 425,
  "cache_hit_rate": 0.34,
  "cost_savings": 8.23,
  "breakdown": [
    {
      "model": "gpt-3.5-turbo",
      "requests": 800,
      "cost": 4.20,
      "tokens": 280000
    },
    {
      "model": "gpt-4",
      "requests": 450,
      "cost": 11.22,
      "tokens": 187500
    }
  ],
  "daily_usage": [
    {
      "date": "2025-01-01",
      "requests": 125,
      "cost": 1.54
    }
  ]
}
```

---

#### GET /analytics/recommendations

Get AI-powered cost optimization recommendations.

**Headers:**
- `X-API-Key: cog_abc123...`

**Response:**
```json
{
  "recommendations": [
    {
      "type": "model_downgrade",
      "title": "Switch to GPT-3.5 for simple queries",
      "description": "45% of your GPT-4 requests are simple Q&A that could use GPT-3.5",
      "potential_savings": 125.50,
      "priority": "high"
    },
    {
      "type": "caching",
      "title": "Enable longer cache TTL",
      "description": "Many similar requests detected, increase cache duration",
      "potential_savings": 42.30,
      "priority": "medium"
    }
  ],
  "total_potential_savings": 167.80
}
```

---

### 🌐 Provider Management

#### POST /providers/

Add a new LLM provider configuration.

**Headers:**
- `X-API-Key: cog_abc123...`

**Request:**
```json
{
  "provider": "openai",
  "api_key": "sk-your-openai-key",
  "priority": 1,
  "enabled": true
}
```

**Response:**
```json
{
  "id": 1,
  "organization_id": 1,
  "provider": "openai",
  "api_key": "sk-...key",
  "priority": 1,
  "enabled": true,
  "created_at": "2025-01-10T12:00:00Z"
}
```

**Priority System:**
- Lower number = higher priority (1 is highest)
- Fallback to next provider if primary fails
- Smart routing uses enabled providers only

---

#### GET /providers/

List all provider configurations.

**Headers:**
- `X-API-Key: cog_abc123...`

**Response:**
```json
[
  {
    "id": 1,
    "provider": "openai",
    "api_key": "sk-...key",
    "priority": 1,
    "enabled": true,
    "created_at": "2025-01-10T12:00:00Z"
  },
  {
    "id": 2,
    "provider": "anthropic",
    "api_key": "sk-ant-...key",
    "priority": 2,
    "enabled": true,
    "created_at": "2025-01-10T12:05:00Z"
  }
]
```

---

#### PUT /providers/{provider_id}

Update provider configuration.

**Headers:**
- `X-API-Key: cog_abc123...`

**Request:**
```json
{
  "enabled": false,
  "priority": 3
}
```

**Response:**
```json
{
  "id": 1,
  "provider": "openai",
  "priority": 3,
  "enabled": false,
  "updated_at": "2025-01-10T13:00:00Z"
}
```

---

#### DELETE /providers/{provider_id}

Remove a provider configuration.

**Headers:**
- `X-API-Key: cog_abc123...`

**Response:**
```json
{
  "message": "Provider deleted successfully"
}
```

---

### 💾 Cache Management

#### GET /cache/stats

Get cache performance statistics.

**Headers:**
- `X-API-Key: cog_abc123...`

**Response:**
```json
{
  "redis": {
    "hits": 1250,
    "misses": 425,
    "hit_rate": 0.746,
    "total_keys": 1250,
    "memory_usage_mb": 45.2
  },
  "postgresql": {
    "total_cached_responses": 5420,
    "cost_savings": 324.50,
    "oldest_cache_entry": "2024-12-01T10:00:00Z"
  },
  "lifetime_savings": {
    "total_cost_saved": 1250.75,
    "requests_served_from_cache": 8450
  }
}
```

---

#### POST /cache/clear

Clear cache (Redis and/or PostgreSQL).

**Headers:**
- `X-API-Key: cog_abc123...`

**Request:**
```json
{
  "cache_type": "all",
  "pattern": "chat:gpt-4:*"
}
```

**Parameters:**
- `cache_type`: `redis` | `postgresql` | `all` (default: `all`)
- `pattern`: Optional Redis key pattern (default: all keys)

**Response:**
```json
{
  "message": "Cache cleared successfully",
  "redis_keys_deleted": 1250,
  "postgresql_rows_deleted": 5420
}
```

---

### 🔔 Alert Configuration

#### POST /alerts/channels

Configure notification channels (Slack, email, webhook).

**Headers:**
- `X-API-Key: cog_abc123...`

**Request (Slack):**
```json
{
  "channel_type": "slack",
  "configuration": {
    "webhook_url": "https://hooks.slack.com/services/YOUR/WEBHOOK"
  }
}
```

**Request (Email):**
```json
{
  "channel_type": "email",
  "configuration": {
    "email": "alerts@company.com"
  }
}
```

**Request (Webhook):**
```json
{
  "channel_type": "webhook",
  "configuration": {
    "url": "https://your-api.com/webhooks/cognitude",
    "method": "POST",
    "headers": {
      "Authorization": "Bearer your-token"
    }
  }
}
```

**Response:**
```json
{
  "id": 1,
  "organization_id": 1,
  "channel_type": "slack",
  "configuration": {...},
  "enabled": true,
  "created_at": "2025-01-10T12:00:00Z"
}
```

---

#### POST /alerts/config

Configure alert triggers and thresholds.

**Headers:**
- `X-API-Key: cog_abc123...`

**Request:**
```json
{
  "cost_threshold_daily": 100.0,
  "cost_threshold_monthly": 2000.0,
  "rate_limit_warning": 0.8,
  "cache_hit_rate_warning": 0.3,
  "enabled": true
}
```

**Parameters:**
- `cost_threshold_daily`: Alert when daily cost exceeds this (USD)
- `cost_threshold_monthly`: Alert when monthly cost exceeds this (USD)
- `rate_limit_warning`: Alert at this % of rate limit (0-1)
- `cache_hit_rate_warning`: Alert when cache hit rate drops below this (0-1)

**Response:**
```json
{
  "id": 1,
  "organization_id": 1,
  "cost_threshold_daily": 100.0,
  "cost_threshold_monthly": 2000.0,
  "rate_limit_warning": 0.8,
  "cache_hit_rate_warning": 0.3,
  "enabled": true,
  "created_at": "2025-01-10T12:00:00Z"
}
```

**Alert Examples:**

Slack message when cost threshold exceeded:
```
🚨 Cost Alert: Daily Threshold Exceeded
Current: $125.50 / Limit: $100.00
Time: 2025-01-10 14:30:00 UTC
Organization: Acme Corp
```

---

### ⚡ Rate Limiting

#### GET /rate-limits/config

Get current rate limit configuration.

**Headers:**
- `X-API-Key: cog_abc123...`

**Response:**
```json
{
  "organization_id": 1,
  "requests_per_minute": 100,
  "requests_per_hour": 5000,
  "requests_per_day": 100000,
  "enabled": true,
  "current_usage": {
    "minute": 45,
    "hour": 1250,
    "day": 8420
  }
}
```

---

#### PUT /rate-limits/config

Update rate limit configuration.

**Headers:**
- `X-API-Key: cog_abc123...`

**Request:**
```json
{
  "requests_per_minute": 200,
  "requests_per_hour": 10000,
  "requests_per_day": 200000,
  "enabled": true
}
```

**Response:**
```json
{
  "organization_id": 1,
  "requests_per_minute": 200,
  "requests_per_hour": 10000,
  "requests_per_day": 200000,
  "enabled": true,
  "updated_at": "2025-01-10T12:00:00Z"
}
```

**Rate Limit Response (HTTP 429):**
```json
{
  "error": {
    "message": "Rate limit exceeded",
    "type": "rate_limit_error",
    "limit": "100 requests per minute",
    "retry_after": 45
  }
}
```

---

## Pricing Models

Cognitude tracks costs using official provider pricing:

### OpenAI

- **GPT-4 Turbo**: $10/1M input tokens, $30/1M output tokens
- **GPT-3.5 Turbo**: $0.50/1M input tokens, $1.50/1M output tokens

### Anthropic

- **Claude 3 Opus**: $15/1M input tokens, $75/1M output tokens
- **Claude 3 Sonnet**: $3/1M input tokens, $15/1M output tokens
- **Claude 3 Haiku**: $0.25/1M input tokens, $1.25/1M output tokens

### Mistral

- **Mistral Large**: $8/1M input tokens, $24/1M output tokens
- **Mistral Medium**: $2.70/1M input tokens, $8.10/1M output tokens

### Groq

- **Llama 3 70B**: $0.70/1M input tokens, $0.80/1M output tokens
- **Mixtral 8x7B**: $0.24/1M input tokens, $0.24/1M output tokens

---

## Error Responses

All errors return a JSON response with this format:

```json
{
  "error": {
    "message": "Human-readable error message",
    "type": "error_type",
    "code": "ERROR_CODE"
  }
}
```

### Common Error Codes

| HTTP Status | Type                    | Description           |
| ----------- | ----------------------- | --------------------- |
| 400         | `invalid_request_error` | Malformed request     |
| 401         | `authentication_error`  | Invalid API key       |
| 403         | `permission_error`      | Access denied         |
| 404         | `not_found_error`       | Resource not found    |
| 429         | `rate_limit_error`      | Rate limit exceeded   |
| 500         | `api_error`             | Internal server error |
| 503         | `service_unavailable`   | Temporary outage      |

---

## Best Practices

### 1. Cache Optimization

```python
# ✅ Good: Consistent prompt formatting
messages = [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": user_input}
]

# ❌ Bad: Random whitespace prevents cache hits
messages = [
    {"role": "system", "content": f"You are a helpful assistant. "},
    {"role": "user", "content": f" {user_input} "}
]
```

### 2. Smart Routing

```python
# Let Cognitude choose the model
response = requests.post(
    "http://localhost:8000/v1/smart/completions",
    headers={"Authorization": f"Bearer {API_KEY}"},
    json={"messages": messages}
)
# Automatically uses gpt-3.5 for simple queries, gpt-4 for complex ones
```

### 3. Error Handling

```python
try:
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=messages
    )
except OpenAIError as e:
    if e.status_code == 429:
        # Rate limited, retry with backoff
        time.sleep(60)
    elif e.status_code == 503:
        # Provider down, fallback happens automatically
        pass
```

### 4. Cost Monitoring

```python
# Check costs regularly
usage = requests.get(
    "http://localhost:8000/analytics/usage",
    headers={"X-API-Key": API_KEY}
).json()

if usage["total_cost"] > daily_budget:
    # Alert or throttle requests
    pass
```

---

## Migration Guide

### From OpenAI Direct

**Before:**

```python
from openai import OpenAI

client = OpenAI(api_key="sk-openai-key")
response = client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[{"role": "user", "content": "Hello!"}]
)
```

**After:**

```python
from openai import OpenAI

# Only 2 lines change!
client = OpenAI(
    api_key="cog_abc123...",  # ← Change 1: Cognitude API key
    base_url="http://localhost:8000/v1"  # ← Change 2: Point to proxy
)

# Everything else stays the same
response = client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[{"role": "user", "content": "Hello!"}]
)
```

### Cost Comparison

**Direct OpenAI:**

- 1,000 requests × 100 tokens = $0.15
- No caching
- No optimization
- **Monthly cost: $150**

**Through Cognitude:**

- 1,000 requests × 100 tokens = $0.15
- 40% cache hit rate = $0.06 saved
- Smart routing = $0.03 saved
- **Monthly cost: $90 (40% savings)**

---

## Support

- **Documentation**: https://docs.cognitude.io
- **GitHub**: https://github.com/your-org/cognitude
- **Email**: support@cognitude.io

---

## Changelog

### v1.0.0 (January 2025)

- ✅ OpenAI-compatible chat completions
- ✅ Redis + PostgreSQL caching
- ✅ Multi-provider support (OpenAI, Anthropic, Mistral, Groq)
- ✅ Smart model selection
- ✅ Cost tracking and analytics
- ✅ Rate limiting
- ✅ Alert channels (Slack, email, webhook)
- ✅ Usage recommendations

### Coming Soon

- 🔄 Streaming support
- 🔄 Function calling passthrough
- 🔄 Custom model routing rules
- 🔄 A/B testing framework
- 🔄 Advanced analytics dashboard
