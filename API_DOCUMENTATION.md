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

  "created_at": "2025-01-10T12:00:00Z"  "created_at": "2025-11-10T12:00:00Z"

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

````"configuration": {"email": "alerts@company.com"}

  }'

### OpenAI SDK (for chat completions)```



```python**Slack:**

client = OpenAI(

    api_key="cog_abc123...",  # Your Cognitude API key```bash

    base_url="http://localhost:8000/v1"curl -X POST http://localhost:8000/alert-channels/ \

)  -H "X-API-Key: your-api-key" \

```  -H "Content-Type: application/json" \

  -d '{

---    "channel_type": "slack",

    "configuration": {

## API Reference      "webhook_url": "https://hooks.slack.com/services/YOUR/WEBHOOK"

    }

### 🔐 Authentication  }'

````

#### POST /auth/register

### 6. Check for Drift

Register a new organization and receive an API key.

````bash

**Request:**curl http://localhost:8000/drift/models/1/drift/current \

```json  -H "X-API-Key: your-api-key"

{```

  "name": "Acme Corp"

}**Response (Drift Detected):**

````

````json

**Response:**{

```json  "drift_detected": true,

{  "drift_score": 0.678,

  "id": 1,  "p_value": 0.001,

  "name": "Acme Corp",  "samples": 200,

  "api_key": "cog_abc123def456...",  "timestamp": "2025-11-06T10:30:00Z"

  "created_at": "2025-01-10T12:00:00Z"}

}```

````

---

---

## API Reference

### 💬 Chat Completions (OpenAI Compatible)

### Authentication Endpoints

#### POST /v1/chat/completions

#### POST /auth/register

OpenAI-compatible chat completions endpoint with automatic caching and cost tracking.

Register a new organization and receive an API key.

**Headers:**

- `Authorization: Bearer cog_abc123...` (standard OpenAI format)**Request:**

- OR `X-API-Key: cog_abc123...`

`````json

**Request:**{

```json  "name": "Acme Corp"

{}

  "model": "gpt-3.5-turbo",```

  "messages": [

    {"role": "system", "content": "You are a helpful assistant."},**Response:**

    {"role": "user", "content": "What is the capital of France?"}

  ],```json

  "temperature": 0.7,{

  "max_tokens": 150  "name": "Acme Corp",

}  "id": 1,

```  "api_key": "your-api-key"

}

**Response:**```

```json

{---

  "id": "chatcmpl-abc123",

  "object": "chat.completion",### Model Endpoints

  "created": 1704902400,

  "model": "gpt-3.5-turbo",#### POST /models/

  "choices": [

    {Register a new ML model for monitoring.

      "index": 0,

      "message": {**Headers:**

        "role": "assistant",

        "content": "The capital of France is Paris."- `X-API-Key: your-api-key`

      },

      "finish_reason": "stop"**Request:**

    }

  ],```json

  "usage": {{

    "prompt_tokens": 20,  "name": "fraud_detector_v1",

    "completion_tokens": 8,  "version": "1.0.0",

    "total_tokens": 28  "description": "Credit card fraud detection model",

  },  "features": [

  "x_cognitude": {    {

    "cached": false,      "feature_name": "transaction_amount",

    "cost": 0.000042,      "feature_type": "numeric",

    "provider": "openai",      "order": 1

    "cache_key": "chat:gpt-3.5-turbo:hash123"    },

  }    {

}      "feature_name": "merchant_category",

```      "feature_type": "categorical",

      "order": 2

**Caching Behavior:**    }

- Identical requests return cached responses instantly (0ms latency)  ]

- Redis cache: 1 hour TTL for fast access}

- PostgreSQL cache: Long-term storage for analytics```

- Costs $0 when served from cache

**Response:**

**Supported Parameters:**

- `model` (required): Model name (gpt-4, gpt-3.5-turbo, claude-3-opus, etc.)```json

- `messages` (required): Array of message objects{

- `temperature`: 0-2, controls randomness  "name": "fraud_detector_v1",

- `max_tokens`: Maximum tokens to generate  "version": "1.0.0",

- `top_p`: Nucleus sampling parameter  "description": "Credit card fraud detection model",

- `frequency_penalty`: -2 to 2  "id": 1,

- `presence_penalty`: -2 to 2  "organization_id": 1,

- `stream`: Boolean (streaming not yet supported)  "created_at": "2025-11-06T10:30:00Z",

  "updated_at": "2025-11-06T10:30:00Z",

---  "features": [...]

}

### 🧠 Smart Routing```



#### POST /v1/smart/completions#### GET /models/



Auto-select the cheapest model that can handle the task complexity.List all models for your organization.



**Headers:****Query Parameters:**

- `Authorization: Bearer cog_abc123...`

- `skip` (int, default: 0) - Pagination offset

**Request:**- `limit` (int, default: 100) - Max results per page

```json

{**Response:**

  "messages": [

    {"role": "user", "content": "What is 2+2?"}```json

  ],[

  "temperature": 0.7  {

}    "id": 1,

```    "name": "fraud_detector_v1",

    "version": "1.0.0",

**Response:**    "organization_id": 1,

```json    "features": [...]

{  }

  "id": "chatcmpl-abc123",]

  "model": "gpt-3.5-turbo",```

  "choices": [...],

  "usage": {...},#### PUT /models/{model_id}/features/{feature_id}

  "x_cognitude": {

    "cached": false,Update baseline statistics for a model feature.

    "cost": 0.000012,

    "provider": "openai",**Request:**

    "selected_model": "gpt-3.5-turbo",

    "complexity_score": 0.15,```json

    "reasoning": "Simple arithmetic, using cheapest model"{

  }  "baseline_stats": {

}    "samples": [0.5, 0.52, 0.48, 0.51, ...]

```  }

}

**How it Works:**```

- Analyzes prompt complexity (length, keywords, structure)

- Selects cheapest model that can handle the taskThe `samples` array should contain 50-100 prediction values from your baseline period.

- Simple queries → gpt-3.5-turbo (cheap)

- Complex queries → gpt-4 (expensive but needed)---

- **Typical savings: 30-50% vs always using GPT-4**

### Prediction Endpoints

---

#### POST /predictions/models/{model_id}/predictions

### 📊 Analytics

Log one or more predictions.

#### GET /analytics/usage

**Headers:**

Get usage metrics and cost breakdown.

- `X-API-Key: your-api-key`

**Headers:**

- `X-API-Key: cog_abc123...`**Request (Batch):**



**Query Parameters:**```json

- `start_date`: ISO 8601 date (default: 7 days ago)[

- `end_date`: ISO 8601 date (default: now)  {

- `group_by`: `day` | `model` | `provider` (default: `day`)    "features": { "transaction_amount": 150.0, "merchant_category": "grocery" },

    "prediction_value": 0.05,

**Request:**    "actual_value": 0.0,

```bash    "timestamp": "2025-11-06T10:30:00Z"

curl "http://localhost:8000/analytics/usage?start_date=2025-01-01&end_date=2025-01-10&group_by=model" \  },

  -H "X-API-Key: cog_abc123..."  {

```    "features": {

      "transaction_amount": 250.0,

**Response:**      "merchant_category": "electronics"

```json    },

{    "prediction_value": 0.15,

  "total_requests": 1250,    "actual_value": 0.0,

  "total_cost": 15.42,    "timestamp": "2025-11-06T10:31:00Z"

  "cache_hits": 425,  }

  "cache_hit_rate": 0.34,]

  "cost_savings": 8.23,```

  "breakdown": [

    {**Field Descriptions:**

      "model": "gpt-3.5-turbo",

      "requests": 800,- `features` (required): Dict of feature name → value

      "cost": 4.20,- `prediction_value` (required): Model output (float)

      "tokens": 280000- `actual_value` (optional): Ground truth for later analysis

    },- `timestamp` (optional): ISO 8601 timestamp (defaults to now)

    {

      "model": "gpt-4",**Response:**

      "requests": 450,

      "cost": 11.22,```json

      "tokens": 187500[

    }  {

  ],    "id": 1,

  "daily_usage": [    "model_id": 1,

    {    "prediction_value": 0.05,

      "date": "2025-01-01",    "actual_value": 0.0,

      "requests": 125,    "time": "2025-11-06T10:30:00Z"

      "cost": 1.54  }

    }]

  ]```

}

```---



---### Drift Detection Endpoints



#### GET /analytics/recommendations#### GET /drift/models/{model_id}/drift/current



Get AI-powered cost optimization recommendations.Check current drift status using the Kolmogorov-Smirnov test.



**Headers:****Headers:**

- `X-API-Key: cog_abc123...`

- `X-API-Key: your-api-key`

**Response:**

```json**Response (Drift Detected):**

{

  "recommendations": [```json

    {{

      "type": "model_downgrade",  "drift_detected": true,

      "title": "Switch to GPT-3.5 for simple queries",  "drift_score": 0.678,

      "description": "45% of your GPT-4 requests are simple Q&A that could use GPT-3.5",  "p_value": 0.001,

      "potential_savings": 125.50,  "samples": 200,

      "priority": "high"  "timestamp": "2025-11-06T10:30:00Z"

    },}

    {```

      "type": "caching",

      "title": "Enable longer cache TTL",**Response (No Drift):**

      "description": "Many similar requests detected, increase cache duration",

      "potential_savings": 42.30,```json

      "priority": "medium"{

    }  "drift_detected": false,

  ],  "drift_score": 0.123,

  "total_potential_savings": 167.80  "p_value": 0.342,

}  "samples": 150,

```  "timestamp": "2025-11-06T10:30:00Z"

}

---```



### 🌐 Provider Management**Response (Insufficient Data):**



#### POST /providers/```json

{

Add a new LLM provider configuration.  "drift_detected": false,

  "message": "Not enough recent prediction data to calculate drift, or model baseline is not set. At least 30 predictions are needed in the last 7 days."

**Headers:**}

- `X-API-Key: cog_abc123...````



**Request:****Interpretation:**

```json

{- `drift_detected`: `true` if p-value < 0.05 (statistically significant drift)

  "provider": "openai",- `drift_score`: 0-1 scale, higher = more drift (0.5+ is strong drift)

  "api_key": "sk-your-openai-key",- `p_value`: Statistical significance (< 0.05 = drift detected)

  "priority": 1,- `samples`: Number of predictions used in the calculation

  "enabled": true

}**Requirements:**

`````

- Model must have baseline statistics configured

**Response:**- At least 30 predictions in the last 7 days

```json

{---

  "id": 1,

  "organization_id": 1,### Alert Channel Endpoints

  "provider": "openai",

  "api_key": "sk-...key",#### POST /alert-channels/

  "priority": 1,

  "enabled": true,Configure email or Slack notifications.

  "created_at": "2025-01-10T12:00:00Z"

}**Headers:**

```

- `X-API-Key: your-api-key`

**Priority System:**

- Lower number = higher priority (1 is highest)**Request (Email):**

- Fallback to next provider if primary fails

- Smart routing uses enabled providers only```json

{

--- "channel_type": "email",

"configuration": {

#### GET /providers/ "email": "alerts@company.com"

}

List all provider configurations.}

````

**Headers:**

- `X-API-Key: cog_abc123...`**Request (Slack):**



**Response:**```json

```json{

[  "channel_type": "slack",

  {  "configuration": {

    "id": 1,    "webhook_url": "https://hooks.slack.com/services/YOUR/WEBHOOK/URL"

    "provider": "openai",  }

    "api_key": "sk-...key",}

    "priority": 1,```

    "enabled": true,

    "created_at": "2025-01-10T12:00:00Z"**Response:**

  },

  {```json

    "id": 2,{

    "provider": "anthropic",  "id": 1,

    "api_key": "sk-ant-...key",  "channel_type": "email",

    "priority": 2,  "is_active": true,

    "enabled": true,  "created_at": "2025-11-06T10:30:00Z"

    "created_at": "2025-01-10T12:05:00Z"}

  }```

]

```#### GET /alert-channels/



---List all configured alert channels.



#### PUT /providers/{provider_id}**Response:**



Update provider configuration.```json

[

**Headers:**  {

- `X-API-Key: cog_abc123...`    "id": 1,

    "channel_type": "email",

**Request:**    "is_active": true,

```json    "created_at": "2025-11-06T10:30:00Z",

{    "configured": true

  "enabled": false,  },

  "priority": 3  {

}    "id": 2,

```    "channel_type": "slack",

    "is_active": true,

**Response:**    "created_at": "2025-11-06T10:35:00Z",

```json    "configured": true

{  }

  "id": 1,]

  "provider": "openai",```

  "priority": 3,

  "enabled": false,#### DELETE /alert-channels/{channel_id}

  "updated_at": "2025-01-10T13:00:00Z"

}Remove an alert channel.

````

**Response:**

---

````json

#### DELETE /providers/{provider_id}{

  "success": true,

Remove a provider configuration.  "message": "Alert channel deleted"

}

**Headers:**```

- `X-API-Key: cog_abc123...`

---

**Response:**

```json## Interactive API Documentation

{

  "message": "Provider deleted successfully"Cognitude provides two interactive documentation interfaces:

}

```### Swagger UI



---Visit `http://localhost:8000/docs` for an interactive API explorer where you can:



### 💾 Cache Management- Test all endpoints directly in your browser

- See request/response schemas

#### GET /cache/stats- View detailed examples

- Execute API calls with your API key

Get cache performance statistics.

### ReDoc

**Headers:**

- `X-API-Key: cog_abc123...`Visit `http://localhost:8000/redoc` for a cleaner, printable API reference with:



**Response:**- Clean, organized documentation

```json- Code samples in multiple languages

{- Detailed descriptions and examples

  "redis": {

    "hits": 1250,---

    "misses": 425,

    "hit_rate": 0.746,## Error Codes

    "total_keys": 1250,

    "memory_usage_mb": 45.2| Code | Meaning               | Common Causes                                                 |

  },| ---- | --------------------- | ------------------------------------------------------------- |

  "postgresql": {| 200  | Success               | Request completed successfully                                |

    "total_cached_responses": 5420,| 400  | Bad Request           | Invalid input data or missing required fields                 |

    "cost_savings": 324.50,| 401  | Unauthorized          | Missing or invalid API key                                    |

    "oldest_cache_entry": "2024-12-01T10:00:00Z"| 403  | Forbidden             | Not authorized to access this resource                        |

  },| 404  | Not Found             | Resource doesn't exist or doesn't belong to your organization |

  "lifetime_savings": {| 409  | Conflict              | Resource already exists (e.g., duplicate organization name)   |

    "total_cost_saved": 1250.75,| 500  | Internal Server Error | Server error - contact support if persistent                  |

    "requests_served_from_cache": 8450

  }---

}

```## Rate Limits



---**Current limits (MVP):**



#### POST /cache/clear- 1000 requests per hour per API key

- 10,000 predictions per hour per model

Clear cache (Redis and/or PostgreSQL).- No limit on models per organization



**Headers:**Limits will be enforced in production. Contact sales for enterprise limits.

- `X-API-Key: cog_abc123...`

---

**Request:**

```json## Best Practices

{

  "cache_type": "all",### 1. Batch Predictions

  "pattern": "chat:gpt-4:*"

}Log predictions in batches of 10-100 for better performance:

````

```python

**Parameters:**predictions = [...]  # List of 100 predictions

- `cache_type`: `redis` | `postgresql` | `all` (default: `all`)requests.post(f"{API_URL}/predictions/models/{model_id}/predictions",

- `pattern`: Optional Redis key pattern (default: all keys)              json=predictions, headers=headers)

```

**Response:**

````json### 2. Set Baseline Properly

{

  "message": "Cache cleared successfully",- Log 50-100 predictions from a "known good" period

  "redis_keys_deleted": 1250,- Use predictions when your model was performing well

  "postgresql_rows_deleted": 5420- Update baseline after retraining

}

```### 3. Monitor Multiple Models



---Register separate models for:



### 🔔 Alert Configuration- Different versions of the same model

- Different use cases or datasets

#### POST /alerts/channels- A/B test variants



Configure notification channels (Slack, email, webhook).### 4. Configure Multiple Channels



**Headers:**Set up both email and Slack for redundancy:

- `X-API-Key: cog_abc123...`

- Email for formal records

**Request (Slack):**- Slack for immediate team notifications

```json

{### 5. Check Drift Regularly

  "channel_type": "slack",

  "configuration": {While background checks run every 15 minutes, you can also:

    "webhook_url": "https://hooks.slack.com/services/YOUR/WEBHOOK"

  }- Query drift status before deployments

}- Check after data pipeline changes

```- Monitor after model retraining



**Request (Email):**---

```json

{## Python SDK (Coming Soon)

  "channel_type": "email",

  "configuration": {We're building a Python SDK to make integration even easier:

    "email": "alerts@company.com"

  }```python

}from cognitude import Cognitude

````

dg = Cognitude(api_key="your-api-key")

**Request (Webhook):**

````json# Register model

{model = dg.register_model(

  "channel_type": "webhook",    name="fraud_detector",

  "configuration": {    version="1.0",

    "url": "https://your-api.com/webhooks/cognitude",    features=[{"name": "amount", "type": "numeric"}]

    "method": "POST",)

    "headers": {

      "Authorization": "Bearer your-token"# Log prediction

    }dg.log_prediction(

  }    model_id=model.id,

}    features={"amount": 150},

```    prediction=0.05

)

**Response:**

```json# Check drift

{drift = dg.check_drift(model_id=model.id)

  "id": 1,print(f"Drift detected: {drift.detected}")

  "organization_id": 1,```

  "channel_type": "slack",

  "configuration": {...},Stay tuned!

  "enabled": true,

  "created_at": "2025-01-10T12:00:00Z"---

}

```## Support



---- **Documentation**: https://docs.cognitude.io

- **Email**: support@cognitude.io

#### POST /alerts/config- **GitHub**: https://github.com/bilguungzt/Cognitude

- **Slack Community**: [Join our Slack](https://cognitude.io/slack)

Configure alert triggers and thresholds.

---

**Headers:**

- `X-API-Key: cog_abc123...`## Changelog



**Request:**### v1.0.0 (2025-11-06)

```json

{- Initial MVP release

  "cost_threshold_daily": 100.0,- Model registration and prediction logging

  "cost_threshold_monthly": 2000.0,- KS test-based drift detection

  "rate_limit_warning": 0.8,- Email and Slack notifications

  "cache_hit_rate_warning": 0.3,- API key authentication

  "enabled": true- Background drift checks every 15 minutes

}
````

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
