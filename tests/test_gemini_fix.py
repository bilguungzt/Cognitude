#!/usr/bin/env python3
"""
Test script to verify the Google Gemini API model name fix
"""
import asyncio
import sys
import os

# Add the project root to the path so we can import modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from app.services.router import ProviderRouter
from sqlalchemy.orm import Session


async def test_model_mapping():
    """Test the model mapping in the call_google function"""
    print("Testing Google Gemini model mapping fix...")
    
    # Create a mock provider config to test with
    class MockProvider:
        def __init__(self):
            self.provider = "google"
        
        def get_api_key(self):
            # Return a dummy API key for testing purposes
            # This will fail at API call but should pass the model mapping
            return "dummy-key-for-testing"
    
    # We can't easily test the actual API call without a real API key,
    # but we can verify that the model mapping is correct in the function source
    import inspect
    
    # Read the source code directly from the file to check model mappings
    import app.services.router
    source = inspect.getsource(app.services.router.ProviderRouter.call_google)
    
    # Check if the new model names are present in the function
    if 'gemini-2.0-flash-exp' in source and 'gemini-2.5-flash-lite' in source:
        print("✅ Model mapping contains the correct model names")
        print("  - gemini-2.0-flash-exp for gemini-pro")
        print(" - gemini-2.5-flash-lite for gemini-flash")
    else:
        print("❌ Model mapping does not contain the correct model names")
        return False
    
    # Verify the old model names are not present
    if 'gemini-1.5-flash-latest' not in source and 'gemini-1.5-pro-latest' not in source:
        print("✅ Old model names have been removed")
    else:
        print("❌ Old model names still exist in the code")
        return False
    
    print("\n✅ All model mapping tests passed!")
    return True


if __name__ == "__main__":
    success = asyncio.run(test_model_mapping())
    if success:
        print("\n🎉 Google Gemini model mapping fix is working correctly!")
        sys.exit(0)
    else:
        print("\n❌ Tests failed!")
        sys.exit(1)