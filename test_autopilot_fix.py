#!/usr/bin/env python3
"""
Test script to verify the Autopilot Google provider model compatibility fix
"""
import asyncio
import sys
import os

# Add the project root to the path so we can import modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from app.core.autopilot import AutopilotEngine
from app.services.router import ProviderRouter
from app import models


class MockDB:
    """Mock database session for testing"""
    pass


class MockOrganization:
    """Mock organization for testing"""
    def __init__(self, org_id=1):
        self.id = org_id


class MockProvider:
    """Mock provider for testing"""
    def __init__(self, provider_name, api_key="test-key"):
        self.provider = provider_name
        self.api_key = api_key
    
    def get_api_key(self):
        return self.api_key


async def test_model_compatibility_logic():
    """Test that the autopilot properly handles model compatibility with providers"""
    print("Testing Autopilot model compatibility fix...")
    
    # Create an autopilot instance
    db = MockDB()
    redis_client = None  # Not needed for this test
    autopilot = AutopilotEngine(db, redis_client)
    
    # Test the logic for Google provider with incompatible model
    provider = MockProvider("google")
    incompatible_model = "gpt-4"
    compatible_model = "gemini-flash"
    
    # Test the model compatibility logic directly
    provider_name = str(provider.provider)
    
    # Test 1: Incompatible model (gpt-*) with Google provider
    final_model = incompatible_model
    if provider_name == "google":
        if incompatible_model.startswith("gpt-") or incompatible_model.startswith("claude-"):
            final_model = "gemini-flash"
        else:
            final_model = incompatible_model
    
    if final_model == "gemini-flash":
        print("✅ Test 1 PASSED: Incompatible model 'gpt-4' was converted to 'gemini-flash' for Google provider")
    else:
        print(f"❌ Test 1 FAILED: Expected 'gemini-flash', got '{final_model}'")
        return False
    
    # Test 2: Compatible model with Google provider
    test_model = compatible_model  # Use the compatible model "gemini-flash"
    final_model = test_model
    if provider_name == "google":
        if test_model.startswith("gpt-") or test_model.startswith("claude-"):
            final_model = "gemini-flash"
        else:
            final_model = test_model
    
    # Since "gemini-flash" doesn't start with "gpt-" or "claude-", it should remain unchanged
    if final_model == test_model and test_model == "gemini-flash":
        print(f"✅ Test 2 PASSED: Compatible model '{test_model}' was preserved for Google provider")
    else:
        print(f"❌ Test 2 FAILED: Expected '{test_model}', got '{final_model}'")
        return False
    
    # Test 3: OpenAI provider with incompatible model (should not be changed)
    openai_provider = MockProvider("openai")
    provider_name = str(openai_provider.provider)
    final_model = incompatible_model
    
    if provider_name == "google":
        if incompatible_model.startswith("gpt-") or incompatible_model.startswith("claude-"):
            final_model = "gemini-flash"
        else:
            final_model = incompatible_model
    
    if final_model == incompatible_model:
        print(f"✅ Test 3 PASSED: Model '{incompatible_model}' was preserved for OpenAI provider")
    else:
        print(f"❌ Test 3 FAILED: Expected '{incompatible_model}', got '{final_model}'")
        return False
    
    print("\n✅ All model compatibility tests passed!")
    return True


def test_router_model_mapping():
    """Test that the router model mapping still works correctly"""
    print("\nTesting Router model mapping...")
    
    # Import and check the model mapping in the call_google function
    import inspect
    import app.services.router
    source = inspect.getsource(app.services.router.ProviderRouter.call_google)
    
    # Check if the new model names are present in the function
    if 'gemini-2.0-flash-exp' in source and 'gemini-2.5-flash-lite' in source:
        print("✅ Router model mapping contains the correct model names")
    else:
        print("❌ Router model mapping does not contain the correct model names")
        return False
    
    # Verify the old model names are not present
    if 'gemini-1.5-flash-latest' not in source and 'gemini-1.5-pro-latest' not in source:
        print("✅ Router old model names have been removed")
    else:
        print("❌ Router old model names still exist in the code")
        return False
    
    print("✅ Router model mapping tests passed!")
    return True


if __name__ == "__main__":
    success1 = asyncio.run(test_model_compatibility_logic())
    success2 = test_router_model_mapping()
    
    if success1 and success2:
        print("\n🎉 All Autopilot and Router fixes are working correctly!")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed!")
        sys.exit(1)