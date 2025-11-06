#!/usr/bin/env python3
"""
Simple script to test drift detection by logging predictions
"""

import requests
import random
from datetime import datetime, timedelta

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


def check_drift(model_id):
    """Check current drift status"""
    url = f"{API_URL}/drift/models/{model_id}/drift/current"
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        drift_data = response.json()
        print("\n" + "="*50)
        print("DRIFT STATUS")
        print("="*50)
        
        if drift_data.get('message'):
            print(f"Status: {drift_data['message']}")
        else:
            print(f"Drift Detected: {drift_data['drift_detected']}")
            print(f"Drift Score: {drift_data['drift_score']:.4f}")
            print(f"P-Value: {drift_data['p_value']:.4f}")
            print(f"Samples: {drift_data['samples']}")
        
        print("="*50 + "\n")
        return drift_data
    else:
        print(f"✗ Failed to check drift: {response.status_code}")
        return None

def get_drift_history(model_id):
    """Get drift history"""
    url = f"{API_URL}/drift/models/{model_id}/history?limit=10"
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        history = response.json()
        print(f"\n📊 Drift History ({len(history)} records):")
        for record in history:
            timestamp = datetime.fromisoformat(record['timestamp'].replace('Z', '+00:00'))
            status = "🔴 DRIFT" if record['drift_detected'] else "🟢 OK"
            print(f"  {status} | {timestamp.strftime('%Y-%m-%d %H:%M')} | Score: {record['drift_score']:.3f} | P-value: {record['p_value']:.4f}")
        return history
    else:
        print(f"✗ Failed to get history: {response.status_code}")
        return []

def main():
    print("🚀 DriftGuard - Prediction Logging & Drift Detection Test")
    print("="*60)
    print(f"API URL: {API_URL}")
    print(f"Model ID: {MODEL_ID}")
    print("="*60 + "\n")
    
    # Step 1: Log 40 normal predictions (similar to baseline)
    print("📝 Step 1: Logging 40 NORMAL predictions...")
    normal_predictions = []
    base_time = datetime.utcnow()
    for i in range(40):
        prediction = {
            "features": {
                "age": random.randint(25, 50),
                "income": random.randint(50000, 95000),
                "tenure_months": random.randint(12, 66)
            },
            "prediction_value": round(random.uniform(0.1, 0.5), 3),
            "timestamp": (base_time - timedelta(seconds=i*10)).isoformat() + "Z"  # Recent timestamps
        }
        normal_predictions.append(prediction)
    
    success = log_predictions(normal_predictions, "NORMAL")
    if not success:
        print("Failed to log predictions. Exiting.")
        return
    
    # Step 2: Check drift (should be NO drift)
    print("\n🔍 Step 2: Checking for drift...")
    drift_status = check_drift(MODEL_ID)
    
    # Step 3: Show drift history
    print("\n📊 Step 3: Fetching drift history...")
    history = get_drift_history(MODEL_ID)
    
    # Step 4: Log 40 DRIFTED predictions
    print("\n" + "="*60)
    print("⚠️  Now logging DRIFTED data to trigger drift detection...")
    print("="*60 + "\n")
    
    print("📝 Step 4: Logging 40 DRIFTED predictions...")
    drifted_predictions = []
    for i in range(40):
        prediction = {
            "features": {
                "age": random.randint(60, 80),           # Much older
                "income": random.randint(150000, 250000), # Much higher income
                "tenure_months": random.randint(80, 120)  # Much longer tenure
            },
            "prediction_value": round(random.uniform(0.7, 0.95), 3),  # Higher predictions
            "timestamp": (base_time - timedelta(seconds=(i+40)*10)).isoformat() + "Z"  # Still recent
        }
        drifted_predictions.append(prediction)
    
    success = log_predictions(drifted_predictions, "DRIFTED")
    if not success:
        print("Failed to log drifted predictions. Exiting.")
        return
    
    # Step 5: Check drift again (should detect drift now)
    print("\n🔍 Step 5: Checking for drift again (should detect drift)...")
    drift_status = check_drift(MODEL_ID)
    
    # Step 6: Show updated drift history
    print("\n📊 Step 6: Fetching updated drift history...")
    history = get_drift_history(MODEL_ID)
    
    # Summary
    print("\n" + "="*60)
    print("✅ TEST COMPLETE!")
    print("="*60)
    print(f"\nTotal predictions logged: 80 (40 normal + 40 drifted)")
    print(f"Drift checks performed: 2")
    print(f"Drift history records: {len(history)}")
    
    if drift_status and drift_status.get('drift_detected'):
        print("\n🎉 SUCCESS! Drift was detected in the drifted data!")
    elif drift_status and drift_status.get('message'):
        print(f"\n⚠️  Note: {drift_status['message']}")
    
    print(f"\n📱 View in Browser:")
    print(f"   Model Details: http://localhost:5173/models/{MODEL_ID}")
    print(f"   Drift History: http://localhost:5173/models/{MODEL_ID}/drift")
    print(f"\n🔑 API Key: {API_KEY}")
    print()

if __name__ == "__main__":
    main()
