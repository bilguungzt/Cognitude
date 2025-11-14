"""
Integration tests for the core LLM proxy functionality.
Tests the complete flow from API request to response.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, JSON
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Add a compilation rule for JSONB on SQLite, so that it is treated as JSON.
# This is necessary because the tests use an in-memory SQLite database,
# which does not have a native JSONB type.
@compiles(JSONB, "sqlite")
def compile_jsonb_sqlite(type_, compiler, **kw):
    return "JSON"

from app.main import app
from app.database import Base, get_db
from app import models, security


# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override database dependency for testing."""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


# Apply dependency override
app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def setup_database(monkeypatch):
    """Create fresh database for each test."""
    # Mock password hashing to avoid bcrypt errors in test environment
    def mock_get_password_hash(password: str) -> str:
        return f"hashed-{password[:20]}"  # Use prefix to avoid length issues

    def mock_verify(secret: str, hash: str) -> bool:
        return hash == f"hashed-{secret[:20]}"

    # Mock the security module functions
    monkeypatch.setattr(security, "get_password_hash", mock_get_password_hash)
    monkeypatch.setattr(security, "verify_password", mock_verify)
    
    # Mock the pwd_context functions directly
    import app.models
    monkeypatch.setattr(app.models.pwd_context, "hash", mock_get_password_hash)
    monkeypatch.setattr(app.models.pwd_context, "verify", mock_verify)
    
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def test_organization():
    """Create a test organization with API key."""
    db = TestingSessionLocal()
    
    # Create organization
    api_key = security.create_api_key()
    hashed_key = security.get_password_hash(api_key)
    
    org = models.Organization(
        name="Test Organization",
        api_key_hash=hashed_key
    )
    db.add(org)
    db.commit()
    db.refresh(org)
    
    # Store the plain API key for testing
    org._plain_api_key = api_key
    
    db.close()
    return org


def test_proxy_chat_completions_unauthorized(client):
    """Test that unauthorized requests are rejected."""
    response = client.post(
        "/v1/chat/completions",
        json={
            "model": "gpt-3.5-turbo",
            "messages": [{"role": "user", "content": "Hello!"}]
        }
    )
    
    assert response.status_code == 403
    # Check for either error message format
    detail = response.json()["detail"]
    assert "API Key" in detail or "credentials" in detail


def test_proxy_chat_completions_authorized(client, test_organization):
    """Test successful authorized request (will fail due to no provider config)."""
    response = client.post(
        "/v1/chat/completions",
        headers={"X-API-Key": test_organization._plain_api_key},
        json={
            "model": "gpt-3.5-turbo",
            "messages": [{"role": "user", "content": "Hello!"}]
        }
    )
    
    # Should fail because no provider is configured, but auth should work
    assert response.status_code in [400, 403, 500]  # Various possible errors


def test_list_models_unauthorized(client):
    """Test that model listing requires authentication."""
    response = client.get("/v1/models")
    assert response.status_code == 403


def test_list_models_authorized(client, test_organization):
    """Test model listing with valid API key."""
    response = client.get(
        "/v1/models",
        headers={"X-API-Key": test_organization._plain_api_key}
    )
    
    # Should succeed even without provider config (returns empty list)
    assert response.status_code == 200
    data = response.json()
    assert "object" in data
    assert "data" in data


def test_organization_registration(client):
    """Test organization registration flow."""
    response = client.post(
        "/auth/register",
        json={"name": "New Test Org"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert "name" in data
    assert "api_key" in data
    assert data["name"] == "New Test Org"
    
    # Verify API key format
    api_key = data["api_key"]
    assert len(api_key) > 20  # Should be reasonably long
    assert api_key.isalnum() or "-" in api_key or "_" in api_key  # URL-safe characters


def test_duplicate_organization_name(client):
    """Test that duplicate organization names are rejected."""
    # Register first organization
    client.post("/auth/register", json={"name": "Duplicate Org"})
    
    # Try to register with same name
    response = client.post("/auth/register", json={"name": "Duplicate Org"})
    
    assert response.status_code == 409  # Conflict
    assert "already exists" in response.json()["detail"]


def test_provider_configuration_flow(client, test_organization):
    """Test provider configuration CRUD operations."""
    headers = {"X-API-Key": test_organization._plain_api_key}
    
    # Create provider config
    create_response = client.post(
        "/providers/",
        headers=headers,
        json={
            "provider": "openai",
            "api_key": "test-api-key",
            "enabled": True,
            "priority": 1
        }
    )
    
    assert create_response.status_code == 200
    provider_data = create_response.json()
    provider_id = provider_data["id"]
    
    # List provider configs
    list_response = client.get("/providers/", headers=headers)
    assert list_response.status_code == 200
    providers = list_response.json()
    assert len(providers) > 0
    
    # Update provider config
    update_response = client.put(
        f"/providers/{provider_id}",
        headers=headers,
        json={"enabled": False}
    )
    assert update_response.status_code == 200
    
    # Delete provider config
    delete_response = client.delete(f"/providers/{provider_id}", headers=headers)
    assert delete_response.status_code == 200


def test_rate_limiting(client, test_organization):
    """Test rate limiting functionality."""
    headers = {"X-API-Key": test_organization._plain_api_key}
    
    # Make multiple requests to trigger rate limiting
    responses = []
    for _ in range(5):  # Make 5 requests
        response = client.get("/v1/models", headers=headers)
        responses.append(response.status_code)
    
    # All requests should succeed (rate limit is high)
    assert all(status == 200 for status in responses)


def test_cache_statistics(client, test_organization):
    """Test cache statistics endpoint."""
    headers = {"X-API-Key": test_organization._plain_api_key}
    
    response = client.get("/cache/stats", headers=headers)
    
    # Should succeed even with no cache data
    assert response.status_code == 200
    data = response.json()
    assert "total_entries" in data
    assert "total_hits" in data
    assert "hit_rate" in data


def test_analytics_endpoints(client, test_organization):
    """Test analytics endpoints."""
    headers = {"X-API-Key": test_organization._plain_api_key}
    
    # Test usage analytics
    response = client.get("/analytics/usage", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert "total_requests" in data
    assert "total_cost" in data
    
    # Test provider analytics
    response = client.get("/analytics/usage?group_by=provider", headers=headers)
    assert response.status_code == 200


def test_health_check(client):
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


def test_metrics_dashboard(client, test_organization):
    """Test business metrics dashboard."""
    headers = {"X-API-Key": test_organization._plain_api_key}
    
    response = client.get("/metrics/summary", headers=headers)
    assert response.status_code == 200
    data = response.json()
    
    assert "timestamp" in data
    assert "organization_id" in data
    assert "metrics" in data
    
    metrics = data["metrics"]
    assert "requests" in metrics
    assert "cost" in metrics
    assert "cache" in metrics
    assert "performance" in metrics
    assert "providers" in metrics
    assert "models" in metrics
    assert "errors" in metrics


@pytest.mark.security
def test_api_key_security(client):
    """Test API key security - invalid keys should be rejected."""
    invalid_keys = [
        "",  # Empty
        "short",  # Too short
        "invalid-key-with-special-chars-!@#$%",  # Special chars
        "a" * 1000,  # Too long
    ]
    
    for invalid_key in invalid_keys:
        response = client.get(
            "/v1/models",
            headers={"X-API-Key": invalid_key}
        )
        assert response.status_code == 403


@pytest.mark.security
def test_sql_injection_protection(client, test_organization):
    """Test that SQL injection attempts are prevented."""
    headers = {"X-API-Key": test_organization._plain_api_key}
    
    # Try SQL injection in model parameter
    response = client.post(
        "/v1/chat/completions",
        headers=headers,
        json={
            "model": "gpt-3.5-turbo'; DROP TABLE users; --",
            "messages": [{"role": "user", "content": "test"}]
        }
    )
    
    # Should not crash the database
    assert response.status_code in [400, 403, 422, 500]


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])