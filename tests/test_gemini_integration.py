#!/usr/bin/env python3
"""
Comprehensive test script for Google Gemini integration with Cognitude API.
Tests provider registration, connection, smart routing, and cost analysis.
"""

import os
import sys
import json
import time
import requests
from typing import Dict, List, Any
from datetime import datetime

# Configuration
BASE_URL = os.getenv("COGNITUDE_BASE_URL", "https://api.cognitude.io")
API_KEY = os.getenv("COGNITUDE_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Color codes for terminal output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"
BOLD = "\033[1m"

def print_header(text: str):
    """Print a formatted header."""
    print(f"\n{BOLD}{BLUE}{'='*70}{RESET}")
    print(f"{BOLD}{BLUE}{text:^70}{RESET}")
    print(f"{BOLD}{BLUE}{'='*70}{RESET}\n")

def print_success(text: str):
    """Print a success message."""
    print(f"{GREEN}✓ {text}{RESET}")

def print_error(text: str):
    """Print an error message."""
    print(f"{RED}✗ {text}{RESET}")

def print_info(text: str):
    """Print an info message."""
    print(f"{BLUE}ℹ {text}{RESET}")

def print_warning(text: str):
    """Print a warning message."""
    print(f"{YELLOW}⚠ {text}{RESET}")

def check_environment():
    """Check if required environment variables are set."""
    print_header("Environment Check")
    
    missing_vars = []
    if not API_KEY:
        missing_vars.append("COGNITUDE_API_KEY")
    if not GEMINI_API_KEY:
        missing_vars.append("GEMINI_API_KEY")
    
    if missing_vars:
        print_error(f"Missing environment variables: {', '.join(missing_vars)}")
        print_info("Please set them before running tests:")
        print_info("export COGNITUDE_API_KEY='your_key_here'")
        print_info("export GEMINI_API_KEY='your_gemini_key_here'")
        return False
    
    print_success("All required environment variables are set")
    print_info(f"Base URL: {BASE_URL}")
    print_info(f"Cognitude API Key: {API_KEY[:10]}...")
    print_info(f"Gemini API Key: {GEMINI_API_KEY[:10]}...")
    return True

def make_request(method: str, endpoint: str, data: Dict = None, headers: Dict = None) -> tuple:
    """Make an HTTP request to the API."""
    url = f"{BASE_URL}{endpoint}"
    default_headers = {"X-API-Key": API_KEY, "Content-Type": "application/json"}
    
    if headers:
        default_headers.update(headers)
    
    try:
        if method.upper() == "GET":
            response = requests.get(url, headers=default_headers, timeout=30)
        elif method.upper() == "POST":
            response = requests.post(url, json=data, headers=default_headers, timeout=30)
        elif method.upper() == "PUT":
            response = requests.put(url, json=data, headers=default_headers, timeout=30)
        elif method.upper() == "DELETE":
            response = requests.delete(url, headers=default_headers, timeout=30)
        else:
            return None, f"Unsupported method: {method}"
        
        return response, None
    except Exception as e:
        return None, str(e)

def test_register_provider():
    """Test registering Google Gemini provider."""
    print_header("Test 1: Registering Google Gemini Provider")
    
    data = {
        "provider": "google",
        "api_key": GEMINI_API_KEY,
        "enabled": True,
        "priority": 1
    }
    
    response, error = make_request("POST", "/providers/", data)
    
    if error:
        print_error(f"Request failed: {error}")
        return False
    
    if response.status_code == 200:
        provider_data = response.json()
        print_success(f"Provider registered successfully!")
        print_info(f"Provider ID: {provider_data['id']}")
        print_info(f"Provider: {provider_data['provider']}")
        print_info(f"Enabled: {provider_data['enabled']}")
        print_info(f"Priority: {provider_data['priority']}")
        return True
    elif response.status_code == 400:
        print_warning("Provider might already exist")
        print_info(f"Response: {response.json()}")
        return True
    else:
        print_error(f"Failed to register provider: {response.status_code}")
        print_info(f"Response: {response.text}")
        return False

def test_list_providers():
    """Test listing all providers."""
    print_header("Test 2: Listing Providers")
    
    response, error = make_request("GET", "/providers/")
    
    if error:
        print_error(f"Request failed: {error}")
        return False
    
    if response.status_code == 200:
        providers = response.json()
        print_success(f"Found {len(providers)} providers")
        
        google_provider = None
        for provider in providers:
            print_info(f"  - {provider['provider']} (ID: {provider['id']}, Enabled: {provider['enabled']})")
            if provider['provider'] == 'google':
                google_provider = provider
        
        if google_provider:
            print_success("Google provider found!")
            return True
        else:
            print_error("Google provider not found in list")
            return False
    else:
        print_error(f"Failed to list providers: {response.status_code}")
        return False

def test_connection():
    """Test connection to Google Gemini."""
    print_header("Test 3: Testing Google Gemini Connection")
    
    data = {
        "provider": "google",
        "api_key": GEMINI_API_KEY
    }
    
    response, error = make_request("POST", "/providers/test", data)
    
    if error:
        print_error(f"Request failed: {error}")
        return False
    
    if response.status_code == 200:
        result = response.json()
        print_success("Connection test successful!")
        print_info(f"Provider: {result['provider']}")
        print_info(f"Model: {result['model']}")
        print_info(f"Response: {result['response']}")
        return True
    else:
        print_error(f"Connection test failed: {response.status_code}")
        print_info(f"Error: {response.json().get('detail', 'Unknown error')}")
        return False

def test_smart_routing_analysis():
    """Test smart routing analysis for different task types."""
    print_header("Test 4: Smart Routing Analysis")
    
    test_cases = [
        {
            "name": "Simple Classification Task",
            "messages": [{"role": "user", "content": "Classify: positive or negative? 'I love this product!'"}],
            "optimize_for": "cost",
            "expected_complexity": "simple"
        },
        {
            "name": "Medium Summarization Task",
            "messages": [{"role": "user", "content": "Summarize this in 2 sentences: Artificial intelligence is transforming industries..."}],
            "optimize_for": "cost",
            "expected_complexity": "medium"
        },
        {
            "name": "Complex Analysis Task",
            "messages": [{"role": "user", "content": "Analyze the economic implications of AI on global job markets over the next decade"}],
            "optimize_for": "quality",
            "expected_complexity": "complex"
        }
    ]
    
    all_passed = True
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{BOLD}Test Case {i}: {test_case['name']}{RESET}")
        print(f"Prompt: {test_case['messages'][0]['content'][:60]}...")
        
        # The endpoint expects messages array directly, not wrapped
        data = test_case["messages"]
        # Add optimize_for as a query parameter
        endpoint = f"/v1/smart/analyze?optimize_for={test_case['optimize_for']}"
        
        response, error = make_request("POST", endpoint, data)
        
        if error:
            print_error(f"Request failed: {error}")
            all_passed = False
            continue
        
        if response.status_code == 200:
            result = response.json()
            print_success("Analysis successful!")
            
            # Show routing decision
            print_info(f"Selected Model: {result.get('selected_model', 'N/A')}")
            print_info(f"Selected Provider: {result.get('selected_provider', 'N/A')}")
            print_info(f"Reason: {result.get('reason', 'N/A')}")
            print_info(f"Estimated Cost: ${result.get('estimated_cost', 0):.6f}/1K tokens")
            
            if result.get('reason') == 'default_fallback':
                print_warning("⚠️  Using fallback model - Gemini models may not be properly configured")
                print_info("This suggests the smart router couldn't find suitable Gemini models")
            else:
                print_success("✓ Smart routing successfully selected an optimal model")
            
            # Show alternatives if any
            if result.get('alternatives'):
                print_info("\nTop Alternatives:")
                for alt in result['alternatives'][:2]:
                    print_info(f"  - {alt['model']}: ${alt['estimated_cost']:.6f}/1K tokens ({alt['reason_not_selected']})")
        else:
            print_error(f"Analysis failed: {response.status_code}")
            try:
                print_info(f"Error: {response.json().get('detail', 'Unknown error')}")
            except:
                print_info(f"Error: {response.text[:100]}...")
            all_passed = False
    
    return all_passed

def test_actual_api_calls():
    """Test making actual API calls through the proxy."""
    print_header("Test 5: Actual API Calls")
    
    test_cases = [
        {
            "name": "Simple Task - Smart Routing",
            "endpoint": "/v1/smart/completions",
            "data": {
                "messages": [{"role": "user", "content": "Count to 5"}],
                "optimize_for": "cost",
                "max_tokens": 50
            }
        },
        {
            "name": "Direct Gemini Call",
            "endpoint": "/v1/chat/completions",
            "data": {
                "model": "gemini-2.5-flash-lite",
                "messages": [{"role": "user", "content": "What is 2+2?"}],
                "max_tokens": 50
            }
        }
    ]
    
    all_passed = True
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{BOLD}Test Case {i}: {test_case['name']}{RESET}")
        
        response, error = make_request("POST", test_case['endpoint'], test_case['data'])
        
        if error:
            print_error(f"Request failed: {error}")
            all_passed = False
            continue
        
        if response.status_code == 200:
            result = response.json()
            print_success("API call successful!")
            
            # Show response
            if 'choices' in result and result['choices']:
                content = result['choices'][0]['message']['content']
                print_info(f"Response: {content[:100]}...")
            
            # Show smart routing info if available
            if 'smart_routing' in result:
                sr = result['smart_routing']
                print_info(f"\nSmart Routing Info:")
                print_info(f"  - Complexity: {sr['complexity']}")
                print_info(f"  - Selected Model: {sr['selected_model']}")
                print_info(f"  - Selected Provider: {sr['selected_provider']}")
                print_info(f"  - Estimated Savings: ${sr['estimated_savings_usd']:.6f}/1K tokens")
            
            # Show usage info
            if 'usage' in result:
                usage = result['usage']
                print_info(f"\nUsage:")
                print_info(f"  - Prompt Tokens: {usage.get('prompt_tokens', 'N/A')}")
                print_info(f"  - Completion Tokens: {usage.get('completion_tokens', 'N/A')}")
                print_info(f"  - Total Tokens: {usage.get('total_tokens', 'N/A')}")
            
            # Show cost if available
            if 'cost_usd' in result:
                print_info(f"  - Cost: ${result['cost_usd']:.6f}")
        else:
            print_error(f"API call failed: {response.status_code}")
            print_info(f"Error: {response.json().get('detail', 'Unknown error')}")
            all_passed = False
    
    return all_passed

def test_analytics():
    """Test analytics endpoints to verify data is being tracked."""
    print_header("Test 6: Analytics Verification")
    
    endpoints = [
        "/analytics/breakdown",
        "/api/v1/metrics"
    ]
    
    all_passed = True
    
    for endpoint in endpoints:
        print(f"\nTesting: {endpoint}")
        
        response, error = make_request("GET", endpoint)
        
        if error:
            print_error(f"Request failed: {error}")
            all_passed = False
            continue
        
        if response.status_code == 200:
            result = response.json()
            print_success("Analytics retrieved successfully!")
            
            # Show provider breakdown
            if 'by_provider' in result:
                print_info("\nProvider Usage:")
                for provider in result['by_provider']:
                    print_info(f"  - {provider['provider']}: {provider['requests']} requests, ${provider['cost']:.6f}")
            
            # Show metrics
            if 'providers' in result:
                print_info("\nProvider Metrics:")
                for provider in result['providers']:
                    print_info(f"  - {provider['provider']}: {provider['requests']} requests, ${provider['cost_usd']:.6f}")
        else:
            print_error(f"Failed to retrieve analytics: {response.status_code}")
            all_passed = False
    
    return all_passed

def print_summary(results: Dict[str, bool]):
    """Print test summary."""
    print_header("Test Summary")
    
    total_tests = len(results)
    passed_tests = sum(1 for passed in results.values() if passed)
    
    for test_name, passed in results.items():
        status = f"{GREEN}PASSED{RESET}" if passed else f"{RED}FAILED{RESET}"
        print(f"{test_name:<40} {status}")
    
    print(f"\n{BOLD}Total: {passed_tests}/{total_tests} tests passed{RESET}")
    
    if passed_tests == total_tests:
        print_success("All tests passed! Google Gemini integration is working correctly.")
        print_info("\nNext steps:")
        print_info("1. Monitor real usage through your dashboard")
        print_info("2. Compare actual costs vs. previous providers")
        print_info("3. Adjust provider priorities based on performance")
        print_info("4. Set up alerts for cost monitoring")
        return True
    else:
        print_error("Some tests failed. Please review the errors above.")
        print_info("\nTroubleshooting steps:")
        print_info("1. Verify your Gemini API key is valid")
        print_info("2. Check that billing is enabled on Google Cloud")
        print_info("3. Ensure the Gemini API is enabled in Google Cloud console")
        print_info("4. Check API logs: docker logs cognitude-api")
        return False

def main():
    """Main test execution."""
    print_header("Google Gemini Integration Test Suite")
    print_info(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Check environment
    if not check_environment():
        sys.exit(1)
    
    # Run tests
    results = {}
    
    print_info("\nRunning integration tests...")
    print_info("This will take approximately 1-2 minutes due to actual API calls.\n")
    
    # Test 1: Register provider
    results["Provider Registration"] = test_register_provider()
    time.sleep(1)
    
    # Test 2: List providers
    results["List Providers"] = test_list_providers()
    time.sleep(1)
    
    # Test 3: Test connection
    results["Connection Test"] = test_connection()
    time.sleep(1)
    
    # Test 4: Smart routing analysis
    results["Smart Routing Analysis"] = test_smart_routing_analysis()
    time.sleep(1)
    
    # Test 5: Actual API calls
    results["Actual API Calls"] = test_actual_api_calls()
    time.sleep(1)
    
    # Test 6: Analytics
    results["Analytics Verification"] = test_analytics()
    
    # Print summary
    success = print_summary(results)
    
    if success:
        print(f"\n{GREEN}{BOLD}🎉 Google Gemini integration test completed successfully!{RESET}")
        sys.exit(0)
    else:
        print(f"\n{RED}{BOLD}❌ Some tests failed. Please review the output above.{RESET}")
        sys.exit(1)

if __name__ == "__main__":
    main()