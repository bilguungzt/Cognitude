#!/usr/bin/env python3
"""
Test script to verify alert router consolidation.
This tests the consolidated alert endpoints without requiring a database.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_alert_endpoints_structure():
    """Test that alert endpoints are properly consolidated under /alerts prefix."""
    
    print("Testing alert endpoint structure...")
    
    # Get OpenAPI schema
    response = client.get("/openapi.json")
    assert response.status_code == 200
    
    openapi_schema = response.json()
    paths = openapi_schema.get("paths", {})
    
    # Check that alert endpoints exist under /alerts prefix
    alert_endpoints = [
        "/alerts/channels",
        "/alerts/channels/{channel_id}",
        "/alerts/configs",
        "/alerts/configs/{config_id}",
        "/alerts/test/{channel_id}",
        "/alerts/check"
    ]
    
    for endpoint in alert_endpoints:
        assert endpoint in paths, f"Missing endpoint: {endpoint}"
        print(f"✅ Found endpoint: {endpoint}")
    
    print("\n✅ All alert endpoints are properly consolidated under /alerts prefix!")

def test_alert_channels_post_schema():
    """Test that the alert channels POST endpoint accepts correct schema."""
    
    print("\nTesting alert channels POST schema...")
    
    # Get the schema for POST /alerts/channels
    response = client.get("/openapi.json")
    openapi_schema = response.json()
    
    post_schema = openapi_schema["paths"]["/alerts/channels"]["post"]
    request_body = post_schema.get("requestBody", {})
    
    assert request_body, "POST /alerts/channels should have a request body"
    
    # Check that it accepts channel_type and configuration
    content = request_body.get("content", {})
    json_schema = content.get("application/json", {})
    schema = json_schema.get("schema", {})
    
    # Handle both inline schemas and $ref schemas
    if "$ref" in schema:
        # Resolve the reference
        ref_path = schema["$ref"].replace("#/components/schemas/", "")
        schema = openapi_schema["components"]["schemas"][ref_path]
    
    assert "properties" in schema, f"Schema should have properties, got: {schema}"
    properties = schema["properties"]
    
    assert "channel_type" in properties, "Should have channel_type property"
    assert "configuration" in properties, "Should have configuration property"
    
    print("✅ Alert channels POST schema is correct!")

def test_old_alert_channels_endpoint_gone():
    """Test that the old /alert-channels endpoint is gone."""
    
    print("\nTesting that old endpoint is removed...")
    
    response = client.get("/openapi.json")
    openapi_schema = response.json()
    paths = openapi_schema.get("paths", {})
    
    # The old endpoint should NOT exist
    assert "/alert-channels" not in paths, "Old /alert-channels endpoint should be removed"
    assert "/alert-channels/" not in paths, "Old /alert-channels/ endpoint should be removed"
    
    print("✅ Old /alert-channels endpoints have been removed!")

if __name__ == "__main__":
    try:
        test_alert_endpoints_structure()
        test_alert_channels_post_schema()
        test_old_alert_channels_endpoint_gone()
        
        print("\n🎉 All tests passed! Alert router consolidation is successful.")
        print("\nSummary of changes:")
        print("- ✅ Merged alert_channels.py functionality into alerts.py")
        print("- ✅ Updated endpoints to use /alerts/channels prefix")
        print("- ✅ Removed redundant alert_channels.py file")
        print("- ✅ Updated main.py to remove old router inclusion")
        print("- ✅ Added comprehensive OpenAPI documentation")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)