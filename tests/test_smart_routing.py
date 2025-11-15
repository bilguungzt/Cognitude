#!/usr/bin/env python3
"""
Test script for Smart Routing (Phase 1.2)

This script demonstrates the three smart routing endpoints:
1. /v1/smart/completions - Automatic model selection
2. /v1/smart/analyze - Analysis without calling
3. /v1/smart/info - Documentation

Usage:
    python test_smart_routing.py
"""
import requests
import json
import sys

# Configuration
BASE_URL = "http://localhost:8000"
API_KEY = "test-key-123"  # Replace with your actual API key

def print_section(title):
    """Print a section header"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")

def test_smart_info():
    """Test the /v1/smart/info endpoint"""
    print_section("Test 1: Smart Routing Info")
    
    response = requests.get(
        f"{BASE_URL}/v1/smart/info",
        headers={"X-API-Key": API_KEY}
    )
    
    if response.status_code == 200:
        data = response.json()
        print("✅ Success! Smart routing info retrieved:")
        print(f"\nDescription: {data['description']}")
        print(f"\nOptimization Modes:")
        for mode in data['optimization_modes']:
            print(f"  - {mode['name']}: {mode['description']}")
        print(f"\nExpected Savings: {data['expected_savings']}")
    else:
        print(f"❌ Failed: {response.status_code}")
        print(response.text)
    
    return response.status_code == 200

def test_smart_analyze():
    """Test the /v1/smart/analyze endpoint"""
    print_section("Test 2: Smart Routing Analysis (Simple Task)")
    
    # Simple task: sentiment classification
    simple_prompt = {
        "messages": [
            {"role": "user", "content": "Classify sentiment: I love this product!"}
        ],
        "optimize_for": "cost"
    }
    
    response = requests.post(
        f"{BASE_URL}/v1/smart/analyze",
        headers={
            "X-API-Key": API_KEY,
            "Content-Type": "application/json"
        },
        json=simple_prompt
    )
    
    if response.status_code == 200:
        data = response.json()
        print("✅ Success! Analysis complete:")
        print(f"\n  Complexity: {data['complexity']}")
        print(f"  Selected Model: {data['selected_model']}")
        print(f"  Selected Provider: {data['selected_provider']}")
        print(f"  Estimated Cost: ${data['estimated_cost']:.6f} per 1K tokens")
        print(f"  Estimated Latency: {data['estimated_latency_ms']}ms")
        print(f"  Estimated Savings: ${data['estimated_savings_usd']:.6f}")
        print(f"\n  Explanation: {data['explanation']}")
        
        if data.get('alternatives'):
            print(f"\n  Alternatives considered:")
            for alt in data['alternatives'][:3]:
                print(f"    - {alt['model']}: {alt['reason_not_selected']}")
    else:
        print(f"❌ Failed: {response.status_code}")
        print(response.text)
    
    return response.status_code == 200

def test_complex_analyze():
    """Test analysis with complex task"""
    print_section("Test 3: Smart Routing Analysis (Complex Task)")
    
    # Complex task: in-depth analysis
    complex_prompt = {
        "messages": [
            {
                "role": "user", 
                "content": "Analyze the economic implications of artificial intelligence on labor markets over the next decade. Consider technological displacement, job creation, skill requirements, and policy recommendations."
            }
        ],
        "optimize_for": "quality"
    }
    
    response = requests.post(
        f"{BASE_URL}/v1/smart/analyze",
        headers={
            "X-API-Key": API_KEY,
            "Content-Type": "application/json"
        },
        json=complex_prompt
    )
    
    if response.status_code == 200:
        data = response.json()
        print("✅ Success! Analysis complete:")
        print(f"\n  Complexity: {data['complexity']}")
        print(f"  Selected Model: {data['selected_model']}")
        print(f"  Selected Provider: {data['selected_provider']}")
        print(f"  Quality Score: {data['quality_score']}")
        print(f"  Estimated Cost: ${data['estimated_cost']:.6f} per 1K tokens")
        print(f"\n  Explanation: {data['explanation']}")
    else:
        print(f"❌ Failed: {response.status_code}")
        print(response.text)
    
    return response.status_code == 200

def test_latency_optimize():
    """Test latency optimization"""
    print_section("Test 4: Smart Routing Analysis (Latency Optimization)")
    
    prompt = {
        "messages": [
            {"role": "user", "content": "Summarize in 3 sentences: The quick brown fox jumps over the lazy dog."}
        ],
        "optimize_for": "latency"
    }
    
    response = requests.post(
        f"{BASE_URL}/v1/smart/analyze",
        headers={
            "X-API-Key": API_KEY,
            "Content-Type": "application/json"
        },
        json=prompt
    )
    
    if response.status_code == 200:
        data = response.json()
        print("✅ Success! Analysis complete:")
        print(f"\n  Complexity: {data['complexity']}")
        print(f"  Selected Model: {data['selected_model']}")
        print(f"  Estimated Latency: {data['estimated_latency_ms']}ms")
        print(f"  Estimated Cost: ${data['estimated_cost']:.6f} per 1K tokens")
        print(f"\n  Explanation: {data['explanation']}")
    else:
        print(f"❌ Failed: {response.status_code}")
        print(response.text)
    
    return response.status_code == 200

def test_cost_comparison():
    """Compare costs across optimization modes"""
    print_section("Test 5: Cost Comparison Across Optimization Modes")
    
    test_prompt = {
        "messages": [
            {"role": "user", "content": "Extract the email from: Contact us at support@example.com"}
        ]
    }
    
    modes = ["cost", "latency", "quality"]
    results = []
    
    for mode in modes:
        test_prompt["optimize_for"] = mode
        response = requests.post(
            f"{BASE_URL}/v1/smart/analyze",
            headers={
                "X-API-Key": API_KEY,
                "Content-Type": "application/json"
            },
            json=test_prompt
        )
        
        if response.status_code == 200:
            data = response.json()
            results.append({
                "mode": mode,
                "model": data['selected_model'],
                "cost": data['estimated_cost'],
                "latency": data['estimated_latency_ms'],
                "quality": data.get('quality_score', 0)
            })
    
    if results:
        print("✅ Comparison complete:\n")
        print(f"{'Mode':<12} {'Model':<20} {'Cost ($/1K)':<15} {'Latency (ms)':<15} {'Quality':<10}")
        print("-" * 80)
        for r in results:
            print(f"{r['mode']:<12} {r['model']:<20} ${r['cost']:<14.6f} {r['latency']:<15} {r['quality']:.2f}")
    else:
        print("❌ Failed to get comparison data")
    
    return len(results) == len(modes)

def main():
    """Run all tests"""
    print("\n🚀 Smart Routing Test Suite")
    print("Testing Phase 1.2 implementation...")
    
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
    
    # Run tests
    results = []
    results.append(("Smart Routing Info", test_smart_info()))
    results.append(("Simple Task Analysis", test_smart_analyze()))
    results.append(("Complex Task Analysis", test_complex_analyze()))
    results.append(("Latency Optimization", test_latency_optimize()))
    results.append(("Cost Comparison", test_cost_comparison()))
    
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
    
    if passed == total:
        print("🎉 All tests passed! Smart routing is working correctly.")
        print("\n💡 Next steps:")
        print("   1. Try the actual /v1/smart/completions endpoint")
        print("   2. Compare costs with regular /v1/chat/completions")
        print("   3. Monitor savings in analytics dashboard")
        return 0
    else:
        print("⚠️  Some tests failed. Please check the errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
