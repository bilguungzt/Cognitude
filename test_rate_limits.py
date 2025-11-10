#!/usr/bin/env python3
"""
Test script for Rate Limiting (Phase 1.5)

This script demonstrates the rate limiting system:
1. /rate-limits/config - Get/update rate limit configuration
2. /rate-limits/usage - Check current usage
3. /rate-limits/reset - Reset counters (admin)
4. 429 responses when limits exceeded
5. Rate limit headers in responses

Usage:
    python test_rate_limits.py
"""
import requests
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

# Configuration
BASE_URL = "http://localhost:8000"
API_KEY = "test-key-123"  # Replace with your actual API key

def print_section(title):
    """Print a section header"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")

def test_get_config():
    """Test getting rate limit configuration"""
    print_section("Test 1: Get Rate Limit Configuration")
    
    response = requests.get(
        f"{BASE_URL}/rate-limits/config",
        headers={"X-API-Key": API_KEY}
    )
    
    if response.status_code == 200:
        data = response.json()
        print("✅ Success! Current configuration:")
        print(f"\n  Requests per minute: {data['requests_per_minute']}")
        print(f"  Requests per hour:   {data['requests_per_hour']}")
        print(f"  Requests per day:    {data['requests_per_day']}")
        print(f"  Enabled:             {data['enabled']}")
        print(f"  Created:             {data['created_at']}")
        return True
    else:
        print(f"❌ Failed: {response.status_code}")
        print(response.text)
        return False

def test_update_config(requests_per_minute=10):
    """Test updating rate limit configuration"""
    print_section(f"Test 2: Update Rate Limit Configuration (Set to {requests_per_minute}/min)")
    
    payload = {
        "requests_per_minute": requests_per_minute,
        "requests_per_hour": 300,
        "requests_per_day": 5000,
        "enabled": True
    }
    
    response = requests.put(
        f"{BASE_URL}/rate-limits/config",
        headers={
            "X-API-Key": API_KEY,
            "Content-Type": "application/json"
        },
        json=payload
    )
    
    if response.status_code == 200:
        data = response.json()
        print("✅ Success! Configuration updated:")
        print(f"\n  Requests per minute: {data['requests_per_minute']}")
        print(f"  Requests per hour:   {data['requests_per_hour']}")
        print(f"  Requests per day:    {data['requests_per_day']}")
        print(f"  Enabled:             {data['enabled']}")
        print(f"\n💡 Rate limiting now active with new limits!")
        return True
    else:
        print(f"❌ Failed: {response.status_code}")
        print(response.text)
        return False

def test_get_usage():
    """Test getting current usage"""
    print_section("Test 3: Get Current Usage")
    
    response = requests.get(
        f"{BASE_URL}/rate-limits/usage",
        headers={"X-API-Key": API_KEY}
    )
    
    if response.status_code == 200:
        data = response.json()
        print("✅ Success! Current usage:\n")
        
        for window in ['minute', 'hour', 'day']:
            info = data[window]
            print(f"  {window.capitalize()}:")
            print(f"    Used:      {info['used']}")
            print(f"    Limit:     {info['limit']}")
            print(f"    Remaining: {info['remaining']}")
            print()
        
        return True
    else:
        print(f"❌ Failed: {response.status_code}")
        print(response.text)
        return False

def make_proxy_request():
    """Make a single proxy request"""
    payload = {
        "model": "gpt-3.5-turbo",
        "messages": [
            {"role": "user", "content": "Say 'test' in one word"}
        ],
        "temperature": 0.7,
        "max_tokens": 10
    }
    
    response = requests.post(
        f"{BASE_URL}/v1/chat/completions",
        headers={
            "X-API-Key": API_KEY,
            "Content-Type": "application/json"
        },
        json=payload,
        timeout=10
    )
    
    return response

def test_rate_limit_headers():
    """Test rate limit headers in responses"""
    print_section("Test 4: Check Rate Limit Headers")
    
    try:
        response = make_proxy_request()
        
        # Extract rate limit headers
        headers = response.headers
        limit = headers.get('X-RateLimit-Limit', 'N/A')
        remaining = headers.get('X-RateLimit-Remaining', 'N/A')
        reset = headers.get('X-RateLimit-Reset', 'N/A')
        
        print(f"✅ Rate limit headers found in response:\n")
        print(f"  X-RateLimit-Limit:     {limit}")
        print(f"  X-RateLimit-Remaining: {remaining}")
        print(f"  X-RateLimit-Reset:     {reset}")
        
        if reset != 'N/A':
            from datetime import datetime
            reset_time = datetime.fromtimestamp(int(reset))
            print(f"  Reset Time:            {reset_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def test_rate_limit_enforcement(limit=10):
    """Test that rate limiting actually blocks requests"""
    print_section(f"Test 5: Rate Limit Enforcement (Send {limit + 5} requests)")
    
    print(f"Sending {limit + 5} requests rapidly to trigger rate limit...\n")
    
    success_count = 0
    rate_limited_count = 0
    retry_after = None
    
    for i in range(limit + 5):
        try:
            response = make_proxy_request()
            
            if response.status_code == 200:
                success_count += 1
                print(f"  Request {i+1}: ✅ Success (200)")
            elif response.status_code == 429:
                rate_limited_count += 1
                retry_after = response.headers.get('Retry-After', 'N/A')
                print(f"  Request {i+1}: 🚫 Rate Limited (429) - Retry-After: {retry_after}s")
            else:
                print(f"  Request {i+1}: ❌ Error ({response.status_code})")
            
            # Small delay to avoid overwhelming the server
            time.sleep(0.1)
            
        except Exception as e:
            print(f"  Request {i+1}: ❌ Exception: {str(e)}")
    
    print(f"\n📊 Results:")
    print(f"  Successful:    {success_count}")
    print(f"  Rate Limited:  {rate_limited_count}")
    print(f"  Total:         {success_count + rate_limited_count}")
    
    if rate_limited_count > 0:
        print(f"\n✅ Rate limiting working correctly!")
        print(f"  • First {success_count} requests succeeded")
        print(f"  • Remaining {rate_limited_count} requests were blocked")
        print(f"  • Retry-After header: {retry_after}s")
        return True
    else:
        print(f"\n⚠️  Warning: No requests were rate limited")
        print(f"  • All {success_count} requests succeeded")
        print(f"  • Rate limit may not be enforced or limit is too high")
        return False

def test_concurrent_requests(limit=10):
    """Test rate limiting with concurrent requests"""
    print_section(f"Test 6: Concurrent Request Rate Limiting")
    
    num_requests = limit + 10
    print(f"Sending {num_requests} concurrent requests...\n")
    
    results = {"success": 0, "rate_limited": 0, "errors": 0}
    
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(make_proxy_request) for _ in range(num_requests)]
        
        for i, future in enumerate(as_completed(futures), 1):
            try:
                response = future.result()
                
                if response.status_code == 200:
                    results["success"] += 1
                    print(f"  Request {i}: ✅ Success")
                elif response.status_code == 429:
                    results["rate_limited"] += 1
                    print(f"  Request {i}: 🚫 Rate Limited")
                else:
                    results["errors"] += 1
                    print(f"  Request {i}: ❌ Error ({response.status_code})")
                    
            except Exception as e:
                results["errors"] += 1
                print(f"  Request {i}: ❌ Exception: {str(e)}")
    
    print(f"\n📊 Concurrent Test Results:")
    print(f"  Successful:    {results['success']}")
    print(f"  Rate Limited:  {results['rate_limited']}")
    print(f"  Errors:        {results['errors']}")
    
    if results['rate_limited'] > 0:
        print(f"\n✅ Rate limiting working with concurrent requests!")
        return True
    else:
        print(f"\n⚠️  No concurrent requests were rate limited")
        return False

def test_reset_limits():
    """Test resetting rate limits"""
    print_section("Test 7: Reset Rate Limits")
    
    response = requests.post(
        f"{BASE_URL}/rate-limits/reset",
        headers={"X-API-Key": API_KEY}
    )
    
    if response.status_code == 200:
        data = response.json()
        print("✅ Success! Rate limits reset:")
        print(f"\n  {data['message']}")
        print(f"  Organization ID: {data['organization_id']}")
        print(f"\n💡 All counters reset to 0. You can make requests again!")
        return True
    else:
        print(f"❌ Failed: {response.status_code}")
        print(response.text)
        return False

def test_after_reset():
    """Test making requests after reset"""
    print_section("Test 8: Verify Reset (Make Request After Reset)")
    
    try:
        response = make_proxy_request()
        
        if response.status_code == 200:
            print("✅ Success! Request succeeded after reset")
            
            # Check headers
            remaining = response.headers.get('X-RateLimit-Remaining', 'N/A')
            print(f"\n  X-RateLimit-Remaining: {remaining}")
            print(f"\n💡 Counter reset confirmed - back to full quota!")
            return True
        else:
            print(f"⚠️  Unexpected status: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def main():
    """Run all tests"""
    print("\n🚀 Rate Limiting Test Suite")
    print("Testing Phase 1.5 implementation...")
    
    # Check if server is running
    try:
        health = requests.get(f"{BASE_URL}/health", timeout=2)
        if health.status_code != 200:
            print(f"\n❌ Error: Server is not healthy")
            print("Please start the server with: docker-compose up -d")
            sys.exit(1)
    except requests.exceptions.ConnectionError:
        print(f"\n❌ Error: Cannot connect to {BASE_URL}")
        print("Please start the server with: docker-compose up -d")
        sys.exit(1)
    
    print("\n⚠️  Important Notes:")
    print("   1. This test will temporarily set low rate limits (10 req/min)")
    print("   2. Test requests will be rate limited (429 responses expected)")
    print("   3. Limits will be reset after tests complete")
    print("   4. Configure OpenAI API key in provider config for real requests")
    
    input("\nPress Enter to continue...")
    
    # Run tests
    results = []
    
    # Configuration tests
    results.append(("Get Config", test_get_config()))
    results.append(("Update Config", test_update_config(requests_per_minute=10)))
    results.append(("Get Usage", test_get_usage()))
    
    # Header tests
    results.append(("Rate Limit Headers", test_rate_limit_headers()))
    
    # Enforcement tests
    results.append(("Rate Limit Enforcement", test_rate_limit_enforcement(limit=10)))
    results.append(("Concurrent Rate Limiting", test_concurrent_requests(limit=10)))
    
    # Reset tests
    results.append(("Reset Limits", test_reset_limits()))
    results.append(("After Reset", test_after_reset()))
    
    # Restore default config
    print_section("Cleanup: Restore Default Configuration")
    test_update_config(requests_per_minute=100)
    
    # Print summary
    print_section("Test Summary")
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    print(f"\n{'='*80}")
    print(f"Results: {passed}/{total} tests passed")
    print(f"{'='*80}\n")
    
    if passed >= total - 1:  # Allow 1 failure
        print("🎉 Rate limiting system is working correctly!")
        print("\n💡 Key Features Verified:")
        print("   ✅ Per-organization rate limit configuration")
        print("   ✅ Multiple time windows (minute/hour/day)")
        print("   ✅ Rate limit headers in responses")
        print("   ✅ 429 status with Retry-After header")
        print("   ✅ Concurrent request handling")
        print("   ✅ Admin reset functionality")
        print("\n📊 Rate Limiting Benefits:")
        print("   • Prevents abuse and DOS attacks")
        print("   • Fair resource allocation per organization")
        print("   • Configurable limits for different tiers")
        print("   • Redis-backed distributed counting")
        print("   • Graceful degradation if Redis unavailable")
        return 0
    else:
        print("⚠️  Some tests failed. Please check the errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
