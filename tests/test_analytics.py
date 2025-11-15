#!/usr/bin/env python3
"""
Test script for Enhanced Analytics (Phase 1.3)

This script demonstrates the new analytics endpoints:
1. /analytics/recommendations - AI-powered optimization suggestions
2. /analytics/breakdown - Detailed usage statistics

Usage:
    python test_analytics.py
"""
import requests
import json
import sys
from datetime import datetime, timedelta

# Configuration
BASE_URL = "http://localhost:8000"
API_KEY = "test-key-123"  # Replace with your actual API key

def print_section(title):
    """Print a section header"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")

def test_recommendations():
    """Test the /analytics/recommendations endpoint"""
    print_section("Test 1: Optimization Recommendations")
    
    response = requests.get(
        f"{BASE_URL}/analytics/recommendations",
        headers={"X-API-Key": API_KEY},
        params={"days": 30}
    )
    
    if response.status_code == 200:
        data = response.json()
        print("✅ Success! Recommendations retrieved:")
        print(f"\n📊 Analysis Summary:")
        print(f"  Period: Last {data['analysis_period_days']} days")
        print(f"  Total Recommendations: {data['total_recommendations']}")
        print(f"  Total Potential Monthly Savings: ${data['total_potential_monthly_savings_usd']:.2f}")
        
        if data['recommendations']:
            print(f"\n💡 Top Recommendations:\n")
            for i, rec in enumerate(data['recommendations'][:5], 1):  # Show top 5
                priority_emoji = {'high': '🔴', 'medium': '🟡', 'low': '🟢'}.get(rec['priority'], '⚪')
                print(f"{i}. {priority_emoji} [{rec['priority'].upper()}] {rec['title']}")
                print(f"   {rec['description']}")
                print(f"   💰 Estimated Monthly Savings: ${rec['estimated_monthly_savings_usd']:.2f}")
                print(f"   ✨ Action: {rec['action']}")
                
                if rec.get('details'):
                    print(f"   📈 Details:")
                    for key, value in list(rec['details'].items())[:3]:  # Show first 3 details
                        print(f"      - {key}: {value}")
                print()
        else:
            print("\n✨ Great! No optimization recommendations found.")
            print("   Your usage is already optimized.")
    else:
        print(f"❌ Failed: {response.status_code}")
        print(response.text)
    
    return response.status_code == 200

def test_breakdown():
    """Test the /analytics/breakdown endpoint"""
    print_section("Test 2: Usage Breakdown")
    
    response = requests.get(
        f"{BASE_URL}/analytics/breakdown",
        headers={"X-API-Key": API_KEY},
        params={"days": 30}
    )
    
    if response.status_code == 200:
        data = response.json()
        print("✅ Success! Usage breakdown retrieved:")
        
        # Total stats
        total = data['total']
        print(f"\n📊 Total Usage (Last {data['period_days']} days):")
        print(f"  Requests: {total['requests']:,}")
        print(f"  Cost: ${total['cost_usd']:,.2f}")
        print(f"  Prompt Tokens: {total['prompt_tokens']:,}")
        print(f"  Completion Tokens: {total['completion_tokens']:,}")
        print(f"  Avg Latency: {total['avg_latency_ms']:.0f}ms")
        
        # Cache stats
        cache = data['cache']
        print(f"\n💾 Cache Performance:")
        print(f"  Cached Requests: {cache['cached_requests']:,}")
        print(f"  Cache Hit Rate: {cache['cache_hit_rate']:.1f}%")
        print(f"  Estimated Savings: ${cache['estimated_savings_usd']:,.2f}")
        
        # By model
        if data['by_model']:
            print(f"\n🤖 Top Models by Cost:")
            for model in data['by_model'][:5]:  # Top 5 models
                print(f"  • {model['model']:<20} "
                      f"{model['requests']:>6} requests "
                      f"({model['percentage']:>5.1f}%)  "
                      f"${model['cost_usd']:>8.2f}")
        
        # By provider
        if data['by_provider']:
            print(f"\n🌐 Providers:")
            for provider in data['by_provider']:
                print(f"  • {provider['provider']:<15} "
                      f"{provider['requests']:>6} requests "
                      f"({provider['percentage']:>5.1f}%)  "
                      f"${provider['cost_usd']:>8.2f}")
        
        # Daily trend
        if data['daily_breakdown']:
            print(f"\n📈 Recent Daily Usage:")
            recent_days = data['daily_breakdown'][-7:]  # Last 7 days
            for day in recent_days:
                cache_pct = (day['cached_requests'] / day['requests'] * 100) if day['requests'] > 0 else 0
                print(f"  {day['date']}  "
                      f"{day['requests']:>4} requests  "
                      f"${day['cost_usd']:>6.2f}  "
                      f"({cache_pct:.0f}% cached)")
        
    else:
        print(f"❌ Failed: {response.status_code}")
        print(response.text)
    
    return response.status_code == 200

def test_different_periods():
    """Test recommendations with different time periods"""
    print_section("Test 3: Recommendations Over Different Periods")
    
    periods = [7, 14, 30]
    results = []
    
    for days in periods:
        response = requests.get(
            f"{BASE_URL}/analytics/recommendations",
            headers={"X-API-Key": API_KEY},
            params={"days": days}
        )
        
        if response.status_code == 200:
            data = response.json()
            results.append({
                'days': days,
                'recommendations': data['total_recommendations'],
                'savings': data['total_potential_monthly_savings_usd']
            })
    
    if results:
        print("✅ Period comparison complete:\n")
        print(f"{'Period':<15} {'Recommendations':<20} {'Potential Savings':<20}")
        print("-" * 60)
        for r in results:
            print(f"Last {r['days']} days     {r['recommendations']:<20} ${r['savings']:<19.2f}")
    else:
        print("❌ Failed to get period comparison")
    
    return len(results) == len(periods)

def test_recommendation_types():
    """Categorize recommendations by type"""
    print_section("Test 4: Recommendation Categories")
    
    response = requests.get(
        f"{BASE_URL}/analytics/recommendations",
        headers={"X-API-Key": API_KEY},
        params={"days": 30}
    )
    
    if response.status_code == 200:
        data = response.json()
        
        if data['recommendations']:
            # Group by type
            by_type = {}
            for rec in data['recommendations']:
                rec_type = rec.get('type', 'unknown')
                if rec_type not in by_type:
                    by_type[rec_type] = []
                by_type[rec_type].append(rec)
            
            print("✅ Recommendations by category:\n")
            
            type_labels = {
                'cache_opportunity': '💾 Cache Opportunities',
                'model_downgrade': '🔻 Model Optimization',
                'max_tokens_optimization': '📏 Token Optimization',
                'smart_routing_adoption': '🧠 Smart Routing',
                'prompt_optimization': '✍️  Prompt Engineering'
            }
            
            for rec_type, recs in by_type.items():
                label = type_labels.get(rec_type, rec_type)
                total_savings = sum(r['estimated_monthly_savings_usd'] for r in recs)
                print(f"{label}")
                print(f"  Count: {len(recs)}")
                print(f"  Total Monthly Savings: ${total_savings:.2f}")
                print()
        else:
            print("✨ No recommendations found - usage is optimized!")
    else:
        print(f"❌ Failed: {response.status_code}")
    
    return response.status_code == 200

def test_existing_analytics():
    """Test that existing analytics endpoint still works"""
    print_section("Test 5: Existing Analytics Endpoint")
    
    response = requests.get(
        f"{BASE_URL}/analytics/usage",
        headers={"X-API-Key": API_KEY}
    )
    
    if response.status_code == 200:
        data = response.json()
        print("✅ Success! Existing analytics working:")
        print(f"\n  Total Requests: {data.get('total_requests', 0):,}")
        print(f"  Total Cost: ${data.get('total_cost', 0):,.2f}")
        print(f"  Cache Hit Rate: {data.get('cache_hit_rate', 0):.1f}%")
    else:
        print(f"❌ Failed: {response.status_code}")
        print(response.text)
    
    return response.status_code == 200

def main():
    """Run all tests"""
    print("\n🚀 Enhanced Analytics Test Suite")
    print("Testing Phase 1.3 implementation...")
    
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
    results.append(("Optimization Recommendations", test_recommendations()))
    results.append(("Usage Breakdown", test_breakdown()))
    results.append(("Different Time Periods", test_different_periods()))
    results.append(("Recommendation Categories", test_recommendation_types()))
    results.append(("Existing Analytics", test_existing_analytics()))
    
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
        print("🎉 All tests passed! Enhanced analytics is working correctly.")
        print("\n💡 Next steps:")
        print("   1. Check recommendations to find optimization opportunities")
        print("   2. Review usage breakdown for insights")
        print("   3. Implement suggested optimizations")
        print("   4. Monitor savings over time")
        return 0
    else:
        print("⚠️  Some tests failed. Please check the errors above.")
        print("\n💡 Note: If no recommendations appear, try:")
        print("   1. Make some LLM requests first")
        print("   2. Use expensive models (gpt-4)")
        print("   3. Make duplicate requests")
        print("   4. Wait a few minutes and try again")
        return 1

if __name__ == "__main__":
    sys.exit(main())
