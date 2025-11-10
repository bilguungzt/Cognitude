#!/usr/bin/env python3
"""Quick API functionality tests for Cognitude"""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"

def test_health():
    """Test health endpoint"""
    print("\n🔍 Testing Health Endpoint...")
    response = requests.get(f"{BASE_URL}/health")
    data = response.json()
    print(f"   Status: {data.get('status')}")
    print(f"   Service: {data.get('service')}")
    print(f"   Redis: {data.get('redis', {}).get('status')}")
    assert response.status_code == 200
    assert data["status"] == "healthy"
    print("   ✅ Health check passed!")

def test_root():
    """Test root endpoint"""
    print("\n🔍 Testing Root Endpoint...")
    response = requests.get(f"{BASE_URL}/")
    data = response.json()
    print(f"   Message: {data.get('message')}")
    assert "Cognitude" in data.get("message", "")
    print("   ✅ Root endpoint passed!")

def test_docs():
    """Test documentation endpoints"""
    print("\n🔍 Testing Documentation Endpoints...")
    
    # Swagger UI
    response = requests.get(f"{BASE_URL}/docs")
    assert response.status_code == 200
    assert "Cognitude" in response.text
    print("   ✅ Swagger UI accessible")
    
    # ReDoc
    response = requests.get(f"{BASE_URL}/redoc")
    assert response.status_code == 200
    print("   ✅ ReDoc accessible")

def test_openapi_schema():
    """Test OpenAPI schema"""
    print("\n🔍 Testing OpenAPI Schema...")
    response = requests.get(f"{BASE_URL}/openapi.json")
    data = response.json()
    print(f"   Title: {data['info']['title']}")
    assert "Cognitude" in data["info"]["title"]
    print("   ✅ OpenAPI schema correct!")

def test_rate_limit_info():
    """Test rate limit endpoint"""
    print("\n🔍 Testing Rate Limit Info...")
    response = requests.get(f"{BASE_URL}/rate-limits/info")
    if response.status_code == 200:
        data = response.json()
        print(f"   Per Minute: {data.get('per_minute')}")
        print(f"   Per Hour: {data.get('per_hour')}")
        print(f"   Per Day: {data.get('per_day')}")
        print("   ✅ Rate limit info accessible!")
    else:
        print(f"   ℹ️  Rate limit endpoint returned {response.status_code}")

if __name__ == "__main__":
    print("="*70)
    print("🧪 Cognitude API Quick Tests")
    print("="*70)
    
    try:
        test_health()
        test_root()
        test_docs()
        test_openapi_schema()
        test_rate_limit_info()
        
        print("\n" + "="*70)
        print("✅ All tests passed!")
        print("="*70)
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
