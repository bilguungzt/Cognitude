#!/usr/bin/env python3
"""
Complete drift detection test workflow:
1. Log normal predictions
2. Set baseline from those predictions
3. Check drift (should be OK)
4. Log drifted predictions
5. Check drift again (should detect drift)
"""

import requests
import random
from datetime import datetime, timedelta
import time

# Configuration
API_URL = "http://localhost:8000"
API_KEY = "uP9eWhBunB3Y2bMRS2_Q9Hdb5zLNhJb12ZlicqQXE_s"
MODEL_ID = 18

headers = {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json"
}

def log_predictions(predictions, batch_name):
    """Log a batch of predictions"""
    print(f"Logging {len(predictions)} {batch_name} predictions...")
    
    response = requests.post(
        f"{API_URL}/predictions/models/{MODEL_ID}/predictions",
        headers=headers,
        json=predictions
    )
    
    if response.status_code in [200, 201]:
        print(f"✓ Successfully logged {len(predictions)} predictions")
        return True
    else:
        print(f"✗ Failed to log predictions: {response.status_code}")
        print(response.text)
        return False

def set_baseline():
    """Set baseline for the model"""
    print("🔧 Setting baseline...")
    
    response = requests.post(
        f"{API_URL}/models/{MODEL_ID}/baseline",
        headers=headers
    )
    
    if response.status_code in [200, 201]:
        result = response.json()
        print(f"✓ Baseline set! Used {result.get('predictions_count')} predictions, updated {result.get('features_updated')} features")
        return True
    else:
        print(f"✗ Failed to set baseline: {response.status_code}")
        print(response.text)
        return False

def check_drift():
    """Check current drift status"""
    response = requests.get(
        f"{API_URL}/drift/models/{MODEL_ID}/drift/current",
        headers=headers
    )
    
    if response.status_code == 200:
        drift_data = response.json()
        print("\n" + "="*60)
        print("DRIFT STATUS")
        print("="*60)
        
        if drift_data.get('message'):
            print(f"Status: {drift_data['message']}")
        else:
            status = "🔴 DRIFT DETECTED" if drift_data['drift_detected'] else "🟢 NO DRIFT"
            print(f"{status}")
            print(f"  Drift Score: {drift_data['drift_score']:.4f}")
            print(f"  P-Value: {drift_data['p_value']:.4f}")
            print(f"  Samples: {drift_data['samples']}")
        
        print("="*60 + "\n")
        return drift_data
    else:
        print(f"✗ Failed to check drift: {response.status_code}")
        return None

def get_drift_history():
    """Get drift history"""
    response = requests.get(
        f"{API_URL}/drift/models/{MODEL_ID}/history?limit=10",
        headers=headers
    )
    
    if response.status_code == 200:
        history = response.json()
        print(f"📊 Drift History ({len(history)} records):")
        for record in history:
            timestamp = datetime.fromisoformat(record['timestamp'].replace('Z', '+00:00'))
            status = "🔴 DRIFT" if record['drift_detected'] else "🟢 OK"
            print(f"  {status} | {timestamp.strftime('%Y-%m-%d %H:%M')} | Score: {record['drift_score']:.3f} | P-value: {record['p_value']:.4f}")
        return history
    else:
        print(f"✗ Failed to get history: {response.status_code}")
        return []

def main():
    print("\n" + "="*70)
    print("🚀 DriftGuard - Complete Drift Detection Test")
    print("="*70)
    print(f"API URL: {API_URL}")
    print(f"Model ID: {MODEL_ID}")
    print("="*70 + "\n")
    
    # STEP 1: Log normal baseline predictions
    print("📝 STEP 1: Logging 50 NORMAL predictions (for baseline)...")
    print("-" * 70)
    normal_predictions = []
    base_time = datetime.utcnow()
    
    for i in range(50):
        prediction = {
            "features": {
                "age": random.randint(25, 50),
                "income": random.randint(50000, 95000),
                "tenure_months": random.randint(12, 66)
            },
            "prediction_value": round(random.uniform(0.15, 0.45), 3),
            "timestamp": (base_time - timedelta(seconds=i*10)).isoformat() + "Z"
        }
        normal_predictions.append(prediction)
    
    if not log_predictions(normal_predictions, "NORMAL"):
        print("❌ Failed to log baseline predictions. Exiting.")
        return
    print()
    
    # STEP 2: Set baseline
    print("📝 STEP 2: Setting baseline from normal predictions...")
    print("-" * 70)
    if not set_baseline():
        print("❌ Failed to set baseline. Exiting.")
        return
    print()
    
    # STEP 3: Check drift (should be NO drift)
    print("📝 STEP 3: Checking drift status (should show NO drift)...")
    print("-" * 70)
    check_drift()
    get_drift_history()
    print()
    
    # STEP 4: Log drifted predictions
    print("📝 STEP 4: Logging 50 DRIFTED predictions...")
    print("-" * 70)
    print("⚠️  These predictions have VERY different values:")
    print("   - Prediction values: 0.7-0.95 (vs baseline 0.15-0.45)")
    print()
    
    drifted_predictions = []
    for i in range(50):
        prediction = {
            "features": {
                "age": random.randint(60, 80),
                "income": random.randint(150000, 250000),
                "tenure_months": random.randint(80, 120)
            },
            "prediction_value": round(random.uniform(0.70, 0.95), 3),  # Much higher
            "timestamp": (base_time - timedelta(seconds=(i+50)*10)).isoformat() + "Z"
        }
        drifted_predictions.append(prediction)
    
    if not log_predictions(drifted_predictions, "DRIFTED"):
        print("❌ Failed to log drifted predictions. Exiting.")
        return
    print()
    
    # STEP 5: Check drift again (should DETECT drift)
    print("📝 STEP 5: Checking drift status (should DETECT drift now)...")
    print("-" * 70)
    drift_status = check_drift()
    get_drift_history()
    print()
    
    # SUMMARY
    print("=" * 70)
    print("✅ TEST COMPLETE!")
    print("=" * 70)
    print(f"\nTotal predictions logged: 100 (50 baseline + 50 drifted)")
    print(f"Baseline predictions: 0.15-0.45 range")
    print(f"Drifted predictions: 0.70-0.95 range")
    
    if drift_status and drift_status.get('drift_detected'):
        print("\n🎉 SUCCESS! Drift was detected!")
        print(f"   Drift Score: {drift_status['drift_score']:.4f}")
        print(f"   P-Value: {drift_status['p_value']:.4f}")
    elif drift_status and not drift_status.get('drift_detected'):
        print("\n⚠️  UNEXPECTED: No drift was detected even with different data")
        print(f"   Drift Score: {drift_status['drift_score']:.4f}")
        print(f"   P-Value: {drift_status['p_value']:.4f}")
        print("   Note: P-value should be < 0.05 for drift detection")
    
    print(f"\n📱 View in Browser:")
    print(f"   Model Details: http://localhost:5173/models/{MODEL_ID}")
    print(f"   Drift History: http://localhost:5173/models/{MODEL_ID}/drift")
    print(f"\n🔑 API Key: {API_KEY}")
    print()

if __name__ == "__main__":
    main()
