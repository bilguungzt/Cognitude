# DriftGuard AI - API Documentation

## Base URL

```
http://localhost:8000  (Development)
https://api.driftguard.ai  (Production)
```

## Authentication

All endpoints (except `/auth/register`) require an API key in the `X-API-Key` header:

```bash
curl -H "X-API-Key: your-api-key-here" https://api.driftguard.ai/models/
```

## Quick Start Guide

### 1. Register Your Organization

```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"name": "Acme Corp"}'
```

**Response:**

```json
{
  "name": "Acme Corp",
  "id": 1,
  "api_key": "deyektwSJJ-abc123..."
}
```

⚠️ **Save your API key!** It's only shown once.

### 2. Register a Model

```bash
curl -X POST http://localhost:8000/models/ \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "fraud_detector_v1",
    "version": "1.0.0",
    "description": "Credit card fraud detection",
    "features": [
      {
        "feature_name": "transaction_amount",
        "feature_type": "numeric",
        "order": 1
      }
    ]
  }'
```

### 3. Log Predictions

```bash
curl -X POST http://localhost:8000/predictions/models/1/predictions \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '[
    {
      "features": {"transaction_amount": 150.0},
      "prediction_value": 0.05,
      "actual_value": 0.0,
      "timestamp": "2025-11-06T10:30:00Z"
    }
  ]'
```

### 4. Set Baseline Statistics

After logging 50-100 "good" predictions, set the baseline:

```bash
curl -X PUT http://localhost:8000/models/1/features/1 \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "baseline_stats": {
      "samples": [0.05, 0.06, 0.04, 0.05, ...]
    }
  }'
```

### 5. Configure Alerts

**Email:**

```bash
curl -X POST http://localhost:8000/alert-channels/ \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "channel_type": "email",
    "configuration": {"email": "alerts@company.com"}
  }'
```

**Slack:**

```bash
curl -X POST http://localhost:8000/alert-channels/ \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "channel_type": "slack",
    "configuration": {
      "webhook_url": "https://hooks.slack.com/services/YOUR/WEBHOOK"
    }
  }'
```

### 6. Check for Drift

```bash
curl http://localhost:8000/drift/models/1/drift/current \
  -H "X-API-Key: your-api-key"
```

**Response (Drift Detected):**

```json
{
  "drift_detected": true,
  "drift_score": 0.678,
  "p_value": 0.001,
  "samples": 200,
  "timestamp": "2025-11-06T10:30:00Z"
}
```

---

## API Reference

### Authentication Endpoints

#### POST /auth/register

Register a new organization and receive an API key.

**Request:**

```json
{
  "name": "Acme Corp"
}
```

**Response:**

```json
{
  "name": "Acme Corp",
  "id": 1,
  "api_key": "your-api-key"
}
```

---

### Model Endpoints

#### POST /models/

Register a new ML model for monitoring.

**Headers:**

- `X-API-Key: your-api-key`

**Request:**

```json
{
  "name": "fraud_detector_v1",
  "version": "1.0.0",
  "description": "Credit card fraud detection model",
  "features": [
    {
      "feature_name": "transaction_amount",
      "feature_type": "numeric",
      "order": 1
    },
    {
      "feature_name": "merchant_category",
      "feature_type": "categorical",
      "order": 2
    }
  ]
}
```

**Response:**

```json
{
  "name": "fraud_detector_v1",
  "version": "1.0.0",
  "description": "Credit card fraud detection model",
  "id": 1,
  "organization_id": 1,
  "created_at": "2025-11-06T10:30:00Z",
  "updated_at": "2025-11-06T10:30:00Z",
  "features": [...]
}
```

#### GET /models/

List all models for your organization.

**Query Parameters:**

- `skip` (int, default: 0) - Pagination offset
- `limit` (int, default: 100) - Max results per page

**Response:**

```json
[
  {
    "id": 1,
    "name": "fraud_detector_v1",
    "version": "1.0.0",
    "organization_id": 1,
    "features": [...]
  }
]
```

#### PUT /models/{model_id}/features/{feature_id}

Update baseline statistics for a model feature.

**Request:**

```json
{
  "baseline_stats": {
    "samples": [0.5, 0.52, 0.48, 0.51, ...]
  }
}
```

The `samples` array should contain 50-100 prediction values from your baseline period.

---

### Prediction Endpoints

#### POST /predictions/models/{model_id}/predictions

Log one or more predictions.

**Headers:**

- `X-API-Key: your-api-key`

**Request (Batch):**

```json
[
  {
    "features": { "transaction_amount": 150.0, "merchant_category": "grocery" },
    "prediction_value": 0.05,
    "actual_value": 0.0,
    "timestamp": "2025-11-06T10:30:00Z"
  },
  {
    "features": {
      "transaction_amount": 250.0,
      "merchant_category": "electronics"
    },
    "prediction_value": 0.15,
    "actual_value": 0.0,
    "timestamp": "2025-11-06T10:31:00Z"
  }
]
```

**Field Descriptions:**

- `features` (required): Dict of feature name → value
- `prediction_value` (required): Model output (float)
- `actual_value` (optional): Ground truth for later analysis
- `timestamp` (optional): ISO 8601 timestamp (defaults to now)

**Response:**

```json
[
  {
    "id": 1,
    "model_id": 1,
    "prediction_value": 0.05,
    "actual_value": 0.0,
    "time": "2025-11-06T10:30:00Z"
  }
]
```

---

### Drift Detection Endpoints

#### GET /drift/models/{model_id}/drift/current

Check current drift status using the Kolmogorov-Smirnov test.

**Headers:**

- `X-API-Key: your-api-key`

**Response (Drift Detected):**

```json
{
  "drift_detected": true,
  "drift_score": 0.678,
  "p_value": 0.001,
  "samples": 200,
  "timestamp": "2025-11-06T10:30:00Z"
}
```

**Response (No Drift):**

```json
{
  "drift_detected": false,
  "drift_score": 0.123,
  "p_value": 0.342,
  "samples": 150,
  "timestamp": "2025-11-06T10:30:00Z"
}
```

**Response (Insufficient Data):**

```json
{
  "drift_detected": false,
  "message": "Not enough recent prediction data to calculate drift, or model baseline is not set. At least 30 predictions are needed in the last 7 days."
}
```

**Interpretation:**

- `drift_detected`: `true` if p-value < 0.05 (statistically significant drift)
- `drift_score`: 0-1 scale, higher = more drift (0.5+ is strong drift)
- `p_value`: Statistical significance (< 0.05 = drift detected)
- `samples`: Number of predictions used in the calculation

**Requirements:**

- Model must have baseline statistics configured
- At least 30 predictions in the last 7 days

---

### Alert Channel Endpoints

#### POST /alert-channels/

Configure email or Slack notifications.

**Headers:**

- `X-API-Key: your-api-key`

**Request (Email):**

```json
{
  "channel_type": "email",
  "configuration": {
    "email": "alerts@company.com"
  }
}
```

**Request (Slack):**

```json
{
  "channel_type": "slack",
  "configuration": {
    "webhook_url": "https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
  }
}
```

**Response:**

```json
{
  "id": 1,
  "channel_type": "email",
  "is_active": true,
  "created_at": "2025-11-06T10:30:00Z"
}
```

#### GET /alert-channels/

List all configured alert channels.

**Response:**

```json
[
  {
    "id": 1,
    "channel_type": "email",
    "is_active": true,
    "created_at": "2025-11-06T10:30:00Z",
    "configured": true
  },
  {
    "id": 2,
    "channel_type": "slack",
    "is_active": true,
    "created_at": "2025-11-06T10:35:00Z",
    "configured": true
  }
]
```

#### DELETE /alert-channels/{channel_id}

Remove an alert channel.

**Response:**

```json
{
  "success": true,
  "message": "Alert channel deleted"
}
```

---

## Interactive API Documentation

DriftGuard provides two interactive documentation interfaces:

### Swagger UI

Visit `http://localhost:8000/docs` for an interactive API explorer where you can:

- Test all endpoints directly in your browser
- See request/response schemas
- View detailed examples
- Execute API calls with your API key

### ReDoc

Visit `http://localhost:8000/redoc` for a cleaner, printable API reference with:

- Clean, organized documentation
- Code samples in multiple languages
- Detailed descriptions and examples

---

## Error Codes

| Code | Meaning               | Common Causes                                                 |
| ---- | --------------------- | ------------------------------------------------------------- |
| 200  | Success               | Request completed successfully                                |
| 400  | Bad Request           | Invalid input data or missing required fields                 |
| 401  | Unauthorized          | Missing or invalid API key                                    |
| 403  | Forbidden             | Not authorized to access this resource                        |
| 404  | Not Found             | Resource doesn't exist or doesn't belong to your organization |
| 409  | Conflict              | Resource already exists (e.g., duplicate organization name)   |
| 500  | Internal Server Error | Server error - contact support if persistent                  |

---

## Rate Limits

**Current limits (MVP):**

- 1000 requests per hour per API key
- 10,000 predictions per hour per model
- No limit on models per organization

Limits will be enforced in production. Contact sales for enterprise limits.

---

## Best Practices

### 1. Batch Predictions

Log predictions in batches of 10-100 for better performance:

```python
predictions = [...]  # List of 100 predictions
requests.post(f"{API_URL}/predictions/models/{model_id}/predictions",
              json=predictions, headers=headers)
```

### 2. Set Baseline Properly

- Log 50-100 predictions from a "known good" period
- Use predictions when your model was performing well
- Update baseline after retraining

### 3. Monitor Multiple Models

Register separate models for:

- Different versions of the same model
- Different use cases or datasets
- A/B test variants

### 4. Configure Multiple Channels

Set up both email and Slack for redundancy:

- Email for formal records
- Slack for immediate team notifications

### 5. Check Drift Regularly

While background checks run every 15 minutes, you can also:

- Query drift status before deployments
- Check after data pipeline changes
- Monitor after model retraining

---

## Python SDK (Coming Soon)

We're building a Python SDK to make integration even easier:

```python
from driftguard import DriftGuard

dg = DriftGuard(api_key="your-api-key")

# Register model
model = dg.register_model(
    name="fraud_detector",
    version="1.0",
    features=[{"name": "amount", "type": "numeric"}]
)

# Log prediction
dg.log_prediction(
    model_id=model.id,
    features={"amount": 150},
    prediction=0.05
)

# Check drift
drift = dg.check_drift(model_id=model.id)
print(f"Drift detected: {drift.detected}")
```

Stay tuned!

---

## Support

- **Documentation**: https://docs.driftguard.ai
- **Email**: support@driftguard.ai
- **GitHub**: https://github.com/bilguungzt/Drift_Guard
- **Slack Community**: [Join our Slack](https://driftguard.ai/slack)

---

## Changelog

### v1.0.0 (2025-11-06)

- Initial MVP release
- Model registration and prediction logging
- KS test-based drift detection
- Email and Slack notifications
- API key authentication
- Background drift checks every 15 minutes
