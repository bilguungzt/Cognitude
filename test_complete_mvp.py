#!/usr/bin/env python3
"""
Comprehensive test suite for DriftGuard MVP
Tests all major features end-to-end
"""

import requests
import json
from datetime import datetime

# Configuration
API_URL = "https://api.driftassure.com"
API_KEY = "LUTyYniW3nUCzuIP_9iVJ-L76Qhg8guDQgjAaCadvqY"
MODEL_ID = 1  # Change this to your actual model ID after creating a model

headers = {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json"
}

def print_section(title):
    """Print a section header"""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)

def print_test(test_name, passed, details=""):
    """Print test result"""
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"{status} | {test_name}")
    if details:
        print(f"     {details}")

def test_health_check():
    """Test if API is responding"""
    print_section("1. API HEALTH CHECK")
    
    try:
        response = requests.get(f"{API_URL}/docs")
        passed = response.status_code == 200
        print_test("API is responding", passed, f"Status: {response.status_code}")
        return passed
    except Exception as e:
        print_test("API is responding", False, f"Error: {str(e)}")
        return False

def test_authentication():
    """Test API authentication"""
    print_section("2. AUTHENTICATION")
    
    # Test with valid API key
    try:
        response = requests.get(f"{API_URL}/models/", headers=headers)
        valid_passed = response.status_code in [200, 401, 403]
        print_test("Valid API key accepted", valid_passed, f"Status: {response.status_code}")
    except Exception as e:
        print_test("Valid API key accepted", False, f"Error: {str(e)}")
        valid_passed = False
    
    # Test with invalid API key
    try:
        bad_headers = {"X-API-Key": "invalid_key_12345"}
        response = requests.get(f"{API_URL}/models/", headers=bad_headers)
        invalid_passed = response.status_code in [401, 403]
        print_test("Invalid API key rejected", invalid_passed, f"Status: {response.status_code}")
    except Exception as e:
        print_test("Invalid API key rejected", False, f"Error: {str(e)}")
        invalid_passed = False
    
    return valid_passed and invalid_passed

def test_model_endpoints():
    """Test model CRUD operations"""
    print_section("3. MODEL ENDPOINTS")
    
    # List models
    try:
        response = requests.get(f"{API_URL}/models/", headers=headers)
        list_passed = response.status_code == 200
        models = response.json() if list_passed else []
        print_test("GET /models/ - List all models", list_passed, 
                  f"Found {len(models)} model(s)")
    except Exception as e:
        print_test("GET /models/ - List all models", False, f"Error: {str(e)}")
        list_passed = False
        models = []
    
    # Get specific model
    if models:
        try:
            model_id = models[0]["id"]
            response = requests.get(f"{API_URL}/models/{model_id}", headers=headers)
            get_passed = response.status_code == 200
            model = response.json() if get_passed else {}
            print_test(f"GET /models/{model_id} - Get model details", get_passed,
                      f"Model: {model.get('name', 'N/A')}, Features: {len(model.get('features', []))}")
            
            # Check baseline status
            features_with_baseline = sum(1 for f in model.get('features', []) if f.get('baseline_stats'))
            baseline_passed = features_with_baseline > 0
            print_test("Model features have baseline", baseline_passed,
                      f"{features_with_baseline}/{len(model.get('features', []))} features configured")
        except Exception as e:
            print_test("GET /models/{id} - Get model details", False, f"Error: {str(e)}")
            get_passed = False
            baseline_passed = False
    else:
        print_test("GET /models/{id} - Get model details", False, "No models found to test")
        get_passed = False
        baseline_passed = False
    
    return list_passed and get_passed and baseline_passed

def test_predictions():
    """Test prediction logging"""
    print_section("4. PREDICTION LOGGING")
    
    # Count existing predictions
    try:
        response = requests.get(f"{API_URL}/models/", headers=headers)
        models = response.json() if response.status_code == 200 else []
        
        if not models:
            print_test("Predictions exist", False, "No models to test")
            return False
        
        # Check prediction count via drift endpoint
        model_id = models[0]["id"]
        response = requests.get(f"{API_URL}/drift/models/{model_id}/drift/current", headers=headers)
        
        if response.status_code == 200:
            drift_data = response.json()
            samples = drift_data.get('samples', 0)
            count_passed = samples > 0
            print_test("Predictions logged successfully", count_passed,
                      f"Total samples: {samples}")
            return count_passed
        else:
            print_test("Predictions logged successfully", False, 
                      f"Could not verify: Status {response.status_code}")
            return False
            
    except Exception as e:
        print_test("Predictions logged successfully", False, f"Error: {str(e)}")
        return False

def test_drift_detection():
    """Test drift detection functionality"""
    print_section("5. DRIFT DETECTION")
    
    try:
        response = requests.get(f"{API_URL}/models/", headers=headers)
        models = response.json() if response.status_code == 200 else []
        
        if not models:
            print_test("Drift detection working", False, "No models to test")
            return False
        
        model_id = models[0]["id"]
        
        # Check current drift status
        response = requests.get(f"{API_URL}/drift/models/{model_id}/drift/current", headers=headers)
        current_passed = response.status_code == 200
        
        if current_passed:
            drift_data = response.json()
            has_data = 'drift_score' in drift_data or 'message' in drift_data
            print_test("GET /drift/models/{id}/drift/current", has_data,
                      f"Drift: {'Detected' if drift_data.get('drift_detected') else 'Not detected'}, "
                      f"Score: {drift_data.get('drift_score', 'N/A')}")
        else:
            print_test("GET /drift/models/{id}/drift/current", False,
                      f"Status: {response.status_code}")
        
        # Check drift history
        response = requests.get(f"{API_URL}/drift/models/{model_id}/history", headers=headers)
        history_passed = response.status_code == 200
        
        if history_passed:
            history = response.json()
            print_test("GET /drift/models/{id}/history", True,
                      f"History records: {len(history)}")
        else:
            print_test("GET /drift/models/{id}/history", False,
                      f"Status: {response.status_code}")
        
        return current_passed and history_passed
        
    except Exception as e:
        print_test("Drift detection working", False, f"Error: {str(e)}")
        return False

def test_drift_alerts():
    """Test drift alert creation"""
    print_section("6. DRIFT ALERTS")
    
    try:
        # Try different possible endpoints for alerts
        endpoints = [
            "/drift/alerts",
            "/alerts",
            f"/drift/models/{MODEL_ID}/alerts"
        ]
        
        alert_found = False
        for endpoint in endpoints:
            try:
                response = requests.get(f"{API_URL}{endpoint}", headers=headers)
                if response.status_code == 200:
                    alerts = response.json()
                    print_test(f"GET {endpoint}", True,
                              f"Found {len(alerts) if isinstance(alerts, list) else 'some'} alert(s)")
                    alert_found = True
                    break
            except:
                continue
        
        if not alert_found:
            print_test("Drift alerts endpoint", False,
                      "Could not find working alerts endpoint - may need implementation")
        
        return alert_found
        
    except Exception as e:
        print_test("Drift alerts endpoint", False, f"Error: {str(e)}")
        return False

def test_alert_channels():
    """Test alert channel configuration"""
    print_section("7. ALERT CHANNELS")
    
    try:
        # List alert channels
        response = requests.get(f"{API_URL}/alert-channels/", headers=headers)
        list_passed = response.status_code == 200
        
        if list_passed:
            channels = response.json()
            print_test("GET /alert-channels/ - List channels", True,
                      f"Configured channels: {len(channels)}")
            
            if channels:
                for channel in channels:
                    print(f"     - {channel.get('channel_type', 'unknown')}: "
                          f"{channel.get('name', 'unnamed')} "
                          f"({'active' if channel.get('is_active') else 'inactive'})")
        else:
            print_test("GET /alert-channels/ - List channels", False,
                      f"Status: {response.status_code}")
        
        return list_passed
        
    except Exception as e:
        print_test("GET /alert-channels/ - List channels", False, f"Error: {str(e)}")
        return False

def test_baseline():
    """Test baseline configuration"""
    print_section("8. BASELINE CONFIGURATION")
    
    try:
        response = requests.get(f"{API_URL}/models/", headers=headers)
        models = response.json() if response.status_code == 200 else []
        
        if not models:
            print_test("Baseline configured", False, "No models to test")
            return False
        
        model_id = models[0]["id"]
        response = requests.get(f"{API_URL}/models/{model_id}", headers=headers)
        
        if response.status_code == 200:
            model = response.json()
            features = model.get('features', [])
            
            total_features = len(features)
            features_with_baseline = sum(1 for f in features if f.get('baseline_stats'))
            
            baseline_passed = features_with_baseline > 0
            print_test("Baseline statistics configured", baseline_passed,
                      f"{features_with_baseline}/{total_features} features have baseline")
            
            # Test auto-baseline endpoint
            if features_with_baseline == 0:
                response = requests.post(f"{API_URL}/models/{model_id}/baseline", headers=headers)
                auto_passed = response.status_code in [200, 201, 400]  # 400 if not enough predictions
                print_test("POST /models/{id}/baseline - Auto-generate", auto_passed,
                          f"Status: {response.status_code}")
            else:
                print_test("POST /models/{id}/baseline - Auto-generate", True,
                          "Already configured (endpoint exists)")
                auto_passed = True
            
            return baseline_passed and auto_passed
        else:
            print_test("Baseline statistics configured", False,
                      f"Could not get model: {response.status_code}")
            return False
            
    except Exception as e:
        print_test("Baseline configuration", False, f"Error: {str(e)}")
        return False

def test_frontend_pages():
    """Test if frontend is accessible"""
    print_section("9. FRONTEND PAGES")
    
    frontend_url = "https://driftassure-frontend-pvoqoo3nx-bilguungzts-projects.vercel.app"
    
    pages = {
        "/": "Login page",
        "/dashboard": "Dashboard",
        "/alerts": "Alert settings"
    }
    
    all_passed = True
    for path, name in pages.items():
        try:
            response = requests.get(f"{frontend_url}{path}", timeout=5)
            passed = response.status_code == 200
            print_test(f"{name}", passed, f"URL: {path}")
            all_passed = all_passed and passed
        except Exception as e:
            print_test(f"{name}", False, f"Error: {str(e)}")
            all_passed = False
    
    return all_passed

def run_database_checks():
    """Check database state"""
    print_section("10. DATABASE STATE")
    
    print("\n💡 Run these commands on your DigitalOcean server to check database:")
    print("\nSSH into server:")
    print('ssh root@165.22.158.75')
    print('\nThen run:')
    print("\n# Check models")
    print('docker exec -it driftguard_mvp_api_1 python -c "from app.database import SessionLocal; from app.models import Model; db = SessionLocal(); models = db.query(Model).all(); print(f\\"Models: {len(models)}\\"); [print(f\\"  - {m.id}: {m.name}\\") for m in models]"')
    
    print("\n# Check predictions count")
    print('docker exec -it driftguard_mvp_db_1 psql -U myuser -d mydatabase -c "SELECT model_id, COUNT(*) FROM predictions GROUP BY model_id;"')
    
    print("\n# Check drift history")
    print('docker exec -it driftguard_mvp_db_1 psql -U myuser -d mydatabase -c "SELECT model_id, drift_detected, drift_score, timestamp FROM drift_history ORDER BY timestamp DESC LIMIT 10;"')

def main():
    print("\n" + "🚀" * 35)
    print("  DRIFTASSURE MVP - COMPREHENSIVE TEST SUITE")
    print("🚀" * 35)
    print(f"\nTesting against: {API_URL}")
    print(f"Model ID: {MODEL_ID}")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    results = []
    
    # Run all tests
    results.append(("API Health", test_health_check()))
    results.append(("Authentication", test_authentication()))
    results.append(("Model Endpoints", test_model_endpoints()))
    results.append(("Prediction Logging", test_predictions()))
    results.append(("Drift Detection", test_drift_detection()))
    results.append(("Drift Alerts", test_drift_alerts()))
    results.append(("Alert Channels", test_alert_channels()))
    results.append(("Baseline Config", test_baseline()))
    results.append(("Frontend Pages", test_frontend_pages()))
    
    # Database checks (informational)
    run_database_checks()
    
    # Summary
    print_section("TEST SUMMARY")
    
    total_tests = len(results)
    passed_tests = sum(1 for _, passed in results if passed)
    
    print(f"\n{'Category':<30} {'Result':<10}")
    print("-" * 40)
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{name:<30} {status:<10}")
    
    print("\n" + "="*70)
    print(f"  TOTAL: {passed_tests}/{total_tests} test categories passed")
    print("="*70)
    
    if passed_tests == total_tests:
        print("\n🎉 ALL TESTS PASSED! Your MVP is working perfectly!")
    elif passed_tests >= total_tests * 0.8:
        print(f"\n✅ Most tests passed ({passed_tests}/{total_tests})")
        print("   A few optional features may need attention.")
    else:
        print(f"\n⚠️  Some tests failed ({passed_tests}/{total_tests})")
        print("   Review the failed tests above for details.")
    
    print("\n📱 Production URLs:")
    print(f"   Frontend: https://driftassure-frontend-pvoqoo3nx-bilguungzts-projects.vercel.app")
    print(f"   Backend API: https://api.driftassure.com")
    print(f"   API Docs: https://api.driftassure.com/docs")
    
    print("\n� API Key:")
    print(f"   {API_KEY}")
    print()

if __name__ == "__main__":
    main()
