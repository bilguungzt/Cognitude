#!/usr/bin/env python3
"""
Verify that the Gemini updates are deployed correctly
"""

import requests
import sys

API_KEY = "8hX-UQX0UOnDXXWTo-fKhQ"
BASE_URL = "https://api.driftassure.com"

headers = {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json"
}

def check_health():
    """Check if the API is responding"""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=10)
        return response.status_code == 200
    except:
        return False

def check_smart_routing():
    """Test if smart routing includes Gemini models"""
    messages = [{"role": "user", "content": "Classify: positive or negative? 'I love this product!'"}]
    
    response = requests.post(
        f"{BASE_URL}/v1/smart/analyze?optimize_for=cost",
        json=messages,
        headers=headers
    )
    
    if response.status_code != 200:
        print(f"❌ API Error: {response.status_code}")
        return False
    
    result = response.json()
    
    # Check if Gemini models are being considered
    if result.get('reason') == 'default_fallback':
        print("❌ Smart routing is using fallback (old code)")
        print(f"   Response: {result}")
        return False
    elif result.get('selected_provider') == 'google':
        print("✅ Smart routing is selecting Gemini models!")
        print(f"   Selected: {result.get('selected_model')}")
        return True
    else:
        print(f"⚠️  Unexpected result: {result}")
        return False

def main():
    print("=== Verifying Gemini Deployment ===\n")
    
    # Check health
    print("1. Checking API health...")
    if check_health():
        print("   ✅ API is responding")
    else:
        print("   ❌ API is not responding")
        return False
    
    # Check smart routing
    print("\n2. Checking smart routing...")
    if check_smart_routing():
        print("   ✅ Gemini models are available in smart routing")
        return True
    else:
        print("   ❌ Smart routing is not using Gemini models")
        print("   This suggests the old code is still running")
        return False

if __name__ == "__main__":
    success = main()
    if success:
        print("\n🎉 Deployment verification PASSED!")
        print("   Gemini integration is working correctly.")
    else:
        print("\n❌ Deployment verification FAILED!")
        print("   The production server may need to be restarted.")
    sys.exit(0 if success else 1)