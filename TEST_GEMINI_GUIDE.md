# Google Gemini Integration Testing Guide

This guide will help you test your API with Google Gemini to verify cost savings and feature functionality.

## Quick Start (5 minutes)

### 1. Set Environment Variables

```bash
# Your Cognitude API key (from your organization)
export COGNITUDE_API_KEY="8hX-UQX0UOnDXXWTo-fKhQ"

# Your Google Gemini API key
export GEMINI_API_KEY="AIzaSyAwCM5JJ9ZgIDqfcFzILwJX8dUm8CIWQH0"
```

### 2. Run the Test Script

```bash
python test_gemini_integration.py
```

## What the Tests Do

The test script runs 5 comprehensive tests:

1. **Provider Registration** - Registers Google Gemini with your API
2. **Connection Test** - Verifies the Gemini API key works
3. **Smart Routing Analysis** - Tests automatic model selection for different tasks
4. **Actual API Calls** - Makes real requests through your proxy
5. **Cost Comparison** - Compares costs across different providers

## Manual Testing (Alternative)

If you prefer to test manually using curl:

### Register Google Provider

```bash
curl -X POST "http://localhost:8000/providers/" \
  -H "X-API-Key: $COGNITUDE_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "google",
    "api_key": "'"$GEMINI_API_KEY"'",
    "enabled": true,
    "priority": 1
  }'
```

### Test Connection

```bash
curl -X POST "http://localhost:8000/providers/test" \
  -H "X-API-Key: $COGNITUDE_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "google",
    "api_key": "'"$GEMINI_API_KEY"'"
  }'
```

### Test Smart Routing

```bash
# Simple task (should use cost-effective model)
curl -X POST "http://localhost:8000/v1/smart/analyze" \
  -H "X-API-Key: $COGNITUDE_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "Classify: positive or negative? I love this!"}],
    "optimize_for": "cost"
  }'

# Complex task (should use higher quality model)
curl -X POST "http://localhost:8000/v1/smart/analyze" \
  -H "X-API-Key: $COGNITUDE_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "Analyze the economic implications of AI on job markets"}],
    "optimize_for": "quality"
  }'
```

### Make Actual API Call

```bash
curl -X POST "http://localhost:8000/v1/smart/completions" \
  -H "X-API-Key: $COGNITUDE_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "Write a haiku about programming"}],
    "optimize_for": "cost",
    "max_tokens": 50
  }'
```

## Expected Results

### Cost Savings

- **Simple tasks**: Should select Gemini 2.5 Flash Lite (~$0.00025/1K tokens)
- **Medium tasks**: May select Gemini 2.5 Flash Lite
- **Complex tasks**: May select Gemini 2.5 Pro (~$0.0020/1K tokens)

### Compared to other providers:

- **OpenAI GPT-4**: ~$0.03/1K tokens (10-85x more expensive)
- **OpenAI GPT-3.5**: ~$0.0005/1K tokens (comparable to Gemini)
- **Anthropic Claude 3 Opus**: ~$0.015/1K tokens (6x more expensive)

### Expected Savings: 30-85% depending on task complexity

## Monitoring Results

After running tests, check your analytics:

```bash
# View usage breakdown
curl -H "X-API-Key: $COGNITUDE_API_KEY" \
  "http://localhost:8000/analytics/breakdown"

# View provider metrics
curl -H "X-API-Key: $COGNITUDE_API_KEY" \
  "http://localhost:8000/api/v1/metrics"
```

## Troubleshooting

### Provider not found error

- Make sure you've registered the Google provider first
- Check that the provider is enabled: `GET /providers/`

### Connection test fails

- Verify your Gemini API key is valid
- Check that billing is enabled on your Google Cloud project
- Ensure the Gemini API is enabled in your Google Cloud console

### No models selected

- Make sure you have at least one provider registered and enabled
- Check that your API key has sufficient permissions

## Next Steps

After successful testing:

1. **Monitor real usage** through your dashboard
2. **Compare actual costs** vs. previous provider usage
3. **Adjust provider priorities** based on performance
4. **Set up alerts** for cost monitoring
5. **Consider using smart routing** as default for all requests

## Support

If you encounter issues:

- Check API logs: `docker logs cognitude-api`
- Verify database connectivity
- Ensure all environment variables are set correctly
- Check provider status in the database
