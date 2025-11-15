import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.main import app 
from app.api.public_benchmarks import generate_benchmarks, get_public_benchmarks
from app.models import LLMRequest
from datetime import datetime, timedelta

client = TestClient(app)

# Mocks for dependencies
@pytest.fixture
def mock_db_session():
    """Fixture for a mocked database session."""
    db = MagicMock(spec=Session)
    
    # Sample data for llm_requests
    mock_requests = [
        LLMRequest(
            id=1,
            organization_id=1,
            provider="openai",
            model="gpt-4",
            cost_usd=0.0015,
            latency_ms=500,
            status_code=200,
            prompt_tokens=10,
            completion_tokens=20,
            total_tokens=30,
            timestamp=datetime.utcnow() - timedelta(minutes=10)
        ),
        LLMRequest(
            id=2,
            organization_id=1,
            provider="openai",
            model="gpt-4",
            cost_usd=0.0025,
            latency_ms=700,
            status_code=200,
            prompt_tokens=10,
            completion_tokens=20,
            total_tokens=30,
            timestamp=datetime.utcnow() - timedelta(minutes=5)
        ),
        LLMRequest(
            id=3,
            organization_id=1,
            provider="openai",
            model="gpt-3.5-turbo",
            cost_usd=0.0005,
            latency_ms=300,
            status_code=200,
            prompt_tokens=10,
            completion_tokens=20,
            total_tokens=30,
            timestamp=datetime.utcnow() - timedelta(minutes=2)
        ),
        LLMRequest(
            id=4,
            organization_id=1,
            provider="openai",
            model="gpt-4",
            cost_usd=0.0035,
            latency_ms=900,
            status_code=500, # Failed request
            prompt_tokens=10,
            completion_tokens=20,
            total_tokens=30,
            timestamp=datetime.utcnow() - timedelta(minutes=1)
        ),
    ]
    
    # Mock the raw SQL execution result
    mock_result = MagicMock()
    mock_result.fetchall.return_value = [
        ("openai", "gpt-4", 0.0025, 700.0, 880.0, 2/3, 3),
        ("openai", "gpt-3.5-turbo", 0.0005, 300.0, 300.0, 1.0, 1),
    ]
    db.execute.return_value = mock_result
    
    return db

@pytest.fixture
def mock_redis_client():
    """Fixture for a mocked Redis client."""
    redis = MagicMock()
    redis.available = True
    redis.redis.get.return_value = None  # Default to cache miss
    return redis

# Unit tests for generate_benchmarks function
def test_generate_benchmarks_logic(mock_db_session, mock_redis_client):
    """
    Tests the core logic of benchmark generation and caching.
    """
    with patch('app.services.redis_cache.redis_cache.redis', mock_redis_client):
        generate_benchmarks(mock_db_session)

        mock_redis_client.set.assert_called_once()
        args, kwargs = mock_redis_client.set.call_args
        
        cached_data = args[1]
        import json
        data = json.loads(cached_data)
        
        assert "benchmarks" in data
        assert len(data["benchmarks"]) == 1
        
        provider_benchmark = data["benchmarks"][0]
        assert provider_benchmark["provider_name"] == "openai"
        assert len(provider_benchmark["models"]) == 2

        gpt4_benchmark = next(m for m in provider_benchmark["models"] if m["model_name"] == "gpt-4")
        assert gpt4_benchmark["metrics"]["avg_cost"] == pytest.approx(0.0025)
        assert gpt4_benchmark["metrics"]["p50_latency"] == pytest.approx(0.7)
        assert gpt4_benchmark["metrics"]["success_rate"] == pytest.approx(66.66, abs=1)

        gpt35_benchmark = next(m for m in provider_benchmark["models"] if m["model_name"] == "gpt-3.5-turbo")
        assert gpt35_benchmark["metrics"]["avg_cost"] == 0.0005
        assert gpt35_benchmark["metrics"]["p50_latency"] == 0.3
        assert gpt35_benchmark["metrics"]["success_rate"] == 100.0

# Integration test for the API endpoint
# Integration test for the API endpoint
def test_get_public_benchmarks_endpoint_cache_miss(mock_db_session, mock_redis_client):
    """
    Tests the /v1/public/benchmarks/realtime endpoint for a cache miss.
    """
    from app.database import get_db

    app.dependency_overrides[get_db] = lambda: mock_db_session
    with patch('app.api.public_benchmarks.redis_cache', mock_redis_client):
        mock_redis_client.redis.get.return_value = None
        response = client.get("/v1/public/benchmarks/realtime")
        assert response.status_code == 404

    # Clean up
    app.dependency_overrides = {}