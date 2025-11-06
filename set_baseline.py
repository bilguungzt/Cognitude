#!/usr/bin/env python3
"""
Set baseline for a model using its existing predictions
"""

import requests

# Configuration
API_URL = "http://localhost:8000"
API_KEY = "uP9eWhBunB3Y2bMRS2_Q9Hdb5zLNhJb12ZlicqQXE_s"
MODEL_ID = 18

headers = {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json"
}

def set_baseline(model_id):
    """Set baseline for a model"""
    print(f"🔧 Setting baseline for model {model_id}...")
    
    response = requests.post(
        f"{API_URL}/models/{model_id}/baseline",
        headers=headers
    )
    
    if response.status_code in [200, 201]:
        result = response.json()
        print(f"✓ Baseline set successfully!")
        print(f"  Predictions used: {result.get('predictions_count', 'N/A')}")
        print(f"  Features updated: {result.get('features_updated', 'N/A')}")
        return True
    else:
        print(f"✗ Failed to set baseline: {response.status_code}")
        print(response.text)
        return False

def main():
    print("🚀 DriftGuard - Set Model Baseline")
    print("="*60)
    print(f"API URL: {API_URL}")
    print(f"Model ID: {MODEL_ID}")
    print("="*60 + "\n")
    
    success = set_baseline(MODEL_ID)
    
    if success:
        print("\n✅ Baseline configuration complete!")
        print("You can now run drift detection on this model.")
    else:
        print("\n❌ Failed to set baseline")

if __name__ == "__main__":
    main()
