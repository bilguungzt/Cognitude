#!/usr/bin/env python3
"""
Quick script to find the correct API endpoint for driftassure.com
"""

import requests
import os

API_KEY = "8hX-UQX0UOnDXXWTo-fKhQ"
GEMINI_API_KEY = "AIzaSyAwCM5JJ9ZgIDqfcFzILwJX8dUm8CIWQH0"

# Possible API endpoints to test
endpoints_to_test = [
    "https://app.driftassure.com/api/v1",
    "https://app.driftassure.com/api",
    "https://api.driftassure.com",
    "https://driftassure.com/api",
    "https://app.driftassure.com",
]

headers = {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json"
}

print("Testing API endpoints for driftassure.com...\n")

for base_url in endpoints_to_test:
    print(f"Testing: {base_url}/providers/")
    try:
        response = requests.get(
            f"{base_url}/providers/",
            headers=headers,
            timeout=10
        )
        print(f"  Status: {response.status_code}")
        if response.status_code == 200:
            print(f"  ✓ SUCCESS! Found working API endpoint: {base_url}")
            print(f"  Response: {response.text[:100]}...")
            break
        elif response.status_code == 401:
            print(f"  ✓ Found endpoint but unauthorized (expected)")
            print(f"  This might be the correct endpoint!")
        elif response.status_code == 404:
            print(f"  - Endpoint not found")
        else:
            print(f"  - Unexpected status: {response.status_code}")
            print(f"  Response: {response.text[:100]}...")
    except Exception as e:
        print(f"  ✗ Failed: {str(e)}")
    print()

print("Testing complete!")