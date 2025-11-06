import os
import sys

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import JSON, create_engine
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


# Add project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.database import Base
from app.main import app
from app.security import get_db
from app import security


# Setup the in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Dependency override to use the test database
def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def mock_hashing(monkeypatch):
    """
    Mocks password hashing and verification to avoid bcrypt error in test environment.
    This is a workaround for an issue where passlib's bcrypt backend detection
    fails, likely due to an outdated bcrypt library, causing a ValueError
    on strings longer than 72 bytes during an internal check.
    """

    def mock_get_password_hash(password: str) -> str:
        # A simple "hash" for testing purposes
        return f"hashed-{password}"

    def mock_verify(secret: str, hash: str) -> bool:
        # A simple "verify" for testing purposes
        return hash == f"hashed-{secret}"

    monkeypatch.setattr(security, "get_password_hash", mock_get_password_hash)
    monkeypatch.setattr(security, "verify_password", mock_verify)


@pytest.fixture()
def client():
    """
    Pytest fixture to create a new database and client for each test.
    """
    Base.metadata.create_all(bind=engine)
    with TestClient(app) as c:
        yield c
    Base.metadata.drop_all(bind=engine)


def test_register_organization(client):
    """
    Test organization registration.
    """
    response = client.post("/auth/register", json={"name": "Test Corp"})
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test Corp"
    assert "api_key" in data


def test_create_model_unauthorized(client):
    """
    Test creating a model without an API key, expecting a 403 Forbidden error.
    """
    model_data = {
        "name": "Test Model",
        "version": "1.0",
        "description": "A test model.",
        "features": [{"feature_name": "age", "feature_type": "numeric", "order": 1}],
    }
    response = client.post("/models/", json=model_data)
    assert response.status_code == 403


def test_create_model_authorized(client):
    """
    Test creating a model with a valid API key.
    """
    # 1. Register an organization to get an API key
    reg_response = client.post("/auth/register", json={"name": "Authorized Corp"})
    assert reg_response.status_code == 200
    api_key = reg_response.json()["api_key"]

    # 2. Use the API key to create a model
    headers = {"X-API-Key": api_key}
    model_data = {
        "name": "Auth Test Model",
        "version": "1.0",
        "description": "An authorized test model.",
        "features": [
            {"feature_name": "income", "feature_type": "numeric", "order": 1},
            {"feature_name": "country", "feature_type": "categorical", "order": 2},
        ],
    }
    model_response = client.post("/models/", headers=headers, json=model_data)

    assert model_response.status_code == 200
    data = model_response.json()
    assert data["name"] == "Auth Test Model"
    assert len(data["features"]) == 2
    assert data["features"][0]["feature_name"] == "income"
