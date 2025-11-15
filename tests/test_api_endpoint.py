#!/usr/bin/env python3
"""
Test the actual API endpoint to see what's happening
"""

import requests
import os
import json

API_KEY = "8hX-UQX0UOnDXXWTo-fKhQ"
BASE_URL = "https://api.cognitude.io"

headers = {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json"
}

# Test the analyze endpoint
messages = [{"role": "user", "content": "Classify: positive or negative? 'I love this product!'"}]

print("=== Testing /v1/smart/analyze endpoint ===\n")

# First, let's check what providers are available
print("1. Checking available providers...")
response = requests.get(f"{BASE_URL}/providers/", headers=headers)
if response.status_code == 200:
    providers = response.json()
    print(f"Found {len(providers)} providers:")
    for p in providers:
        print(f"  - {p['provider']} (ID: {p['id']}, Enabled: {p['enabled']})")
else:
    print(f"Failed to get providers: {response.status_code}")
    print(response.text)

print("\n2. Testing smart routing analyze endpoint...")
response = requests.post(
    f"{BASE_URL}/v1/smart/analyze?optimize_for=cost",
    json=messages,
    headers=headers
)

print(f"Status: {response.status_code}")
if response.status_code == 200:
    result = response.json()
    print(f"Response: {json.dumps(result, indent=2)}")
    
    # Check if it's using fallback
    if result.get('reason') == 'default_fallback':
        print("\n⚠️  FALLBACK DETECTED!")
        print("This means no suitable models were found during routing.")
        print("Possible causes:")
        print("  - available_models list was empty")
        print("  - available_providers list was empty")
        print("  - No models matched the complexity filter")
        print("  - No models matched the provider filter")
else:
    print(f"Error: {response.text}")