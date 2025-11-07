#!/usr/bin/env python3
"""
Send test predictions to enable drift detection
This will send 50 predictions with varied data
"""

import requests
import random
from datetime import datetime, timedelta

# Configuration
API_URL = "https://api.driftassure.com"
API_KEY = "LUTyYniW3nUCzuIP_9iVJ-L76Qhg8guDQgjAaCadvqY"
MODEL_ID = 1

headers = {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json"
}

def generate_predictions(count=50):
    """Generate realistic test predictions"""
    predictions = []
    base_time = datetime.now() - timedelta(days=7)  # Start 7 days ago
    
    for i in range(count):
        # Generate varied but realistic features
        amount = round(random.uniform(10.0, 500.0), 2)
        age = random.randint(18, 75)
        
        # Prediction value (0 or 1 for fraud detection)
        # High amounts slightly more likely to be flagged
        prediction_value = 1 if amount > 350 and random.random() > 0.5 else 0
        
        # Timestamp spread over 7 days
        timestamp = base_time + timedelta(hours=i * 3)
        
        predictions.append({
            "prediction_id": f"test-pred-{i+1}",
            "features": {
                "amount": amount,
                "age": age
            },
            "prediction_value": prediction_value,
            "timestamp": timestamp.strftime("%Y-%m-%dT%H:%M:%SZ")
        })
    
    return predictions

def send_predictions_batch(predictions, batch_size=10):
    """Send predictions in batches"""
    total = len(predictions)
    success_count = 0
    
    print(f"📤 Sending {total} predictions in batches of {batch_size}...\n")
    
    for i in range(0, total, batch_size):
        batch = predictions[i:i+batch_size]
        batch_num = (i // batch_size) + 1
        
        try:
            response = requests.post(
                f"{API_URL}/predictions/models/{MODEL_ID}/predictions",
                headers=headers,
                json=batch
            )
            
            if response.status_code in [200, 201]:
                success_count += len(batch)
                print(f"✅ Batch {batch_num}: Sent {len(batch)} predictions (Total: {success_count}/{total})")
            else:
                print(f"❌ Batch {batch_num}: Failed - Status {response.status_code}")
                print(f"   Error: {response.text[:200]}")
        
        except Exception as e:
            print(f"❌ Batch {batch_num}: Error - {str(e)}")
    
    return success_count

def check_drift_status():
    """Check if drift detection is now active"""
    print("\n🔍 Checking drift detection status...")
    
    try:
        response = requests.get(
            f"{API_URL}/drift/models/{MODEL_ID}/drift/current",
            headers=headers
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n{'='*60}")
            print(f"  DRIFT DETECTION STATUS")
            print(f"{'='*60}")
            print(f"Drift Detected: {data.get('drift_detected', 'N/A')}")
            print(f"Drift Score: {data.get('drift_score', 'N/A')}")
            print(f"Samples: {data.get('samples', 'N/A')}")
            print(f"Message: {data.get('message', 'N/A')}")
            print(f"{'='*60}\n")
        else:
            print(f"❌ Could not check status: {response.status_code}")
    
    except Exception as e:
        print(f"❌ Error checking status: {str(e)}")

def check_baseline():
    """Check if baseline is configured"""
    print("🔍 Checking baseline status...")
    
    try:
        response = requests.get(
            f"{API_URL}/models/{MODEL_ID}",
            headers=headers
        )
        
        if response.status_code == 200:
            model = response.json()
            features = model.get('features', [])
            
            print(f"\n{'='*60}")
            print(f"  BASELINE STATUS")
            print(f"{'='*60}")
            
            for feature in features:
                name = feature.get('name', 'Unknown')
                baseline = feature.get('baseline_stats')
                
                if baseline:
                    print(f"✅ {name}: Baseline configured")
                    print(f"   Mean: {baseline.get('mean', 'N/A')}")
                    print(f"   Std: {baseline.get('std', 'N/A')}")
                else:
                    print(f"❌ {name}: No baseline yet")
            
            print(f"{'='*60}\n")
        else:
            print(f"❌ Could not check baseline: {response.status_code}")
    
    except Exception as e:
        print(f"❌ Error checking baseline: {str(e)}")

def trigger_baseline_generation():
    """Attempt to trigger baseline generation"""
    print("🔄 Attempting to generate baseline...")
    
    try:
        response = requests.post(
            f"{API_URL}/models/{MODEL_ID}/baseline",
            headers=headers
        )
        
        if response.status_code in [200, 201]:
            print("✅ Baseline generation triggered successfully!")
            data = response.json()
            print(f"   Response: {data.get('message', 'Success')}")
        elif response.status_code == 400:
            print("⚠️  Baseline generation not ready yet")
            print(f"   Reason: {response.json().get('detail', 'Unknown')}")
        else:
            print(f"❌ Failed to generate baseline: {response.status_code}")
            print(f"   Error: {response.text[:200]}")
    
    except Exception as e:
        print(f"❌ Error triggering baseline: {str(e)}")

def main():
    print("\n" + "🚀" * 30)
    print("  DRIFTASSURE - SEND TEST PREDICTIONS")
    print("🚀" * 30)
    print(f"\nAPI URL: {API_URL}")
    print(f"Model ID: {MODEL_ID}")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Generate predictions
    predictions = generate_predictions(count=50)
    
    # Send predictions
    success_count = send_predictions_batch(predictions, batch_size=10)
    
    # Summary
    print(f"\n{'='*60}")
    print(f"  SUMMARY")
    print(f"{'='*60}")
    print(f"Total predictions sent: {success_count}/{len(predictions)}")
    
    if success_count >= 30:
        print(f"✅ SUCCESS! You now have enough predictions for drift detection!")
        
        # Try to generate baseline
        print(f"\n{'='*60}\n")
        trigger_baseline_generation()
        
        # Check baseline status
        print(f"\n{'='*60}\n")
        check_baseline()
        
        # Check drift status
        print(f"{'='*60}\n")
        check_drift_status()
        
        print(f"{'='*60}")
        print("\n🎉 NEXT STEPS:")
        print("1. ✅ Predictions sent (enough for baseline)")
        print("2. ⏳ Wait ~15 minutes for automatic drift check")
        print("3. 🌐 Visit your dashboard to see results:")
        print(f"   https://driftassure-frontend-pvoqoo3nx-bilguungzts-projects.vercel.app/dashboard")
        print("4. 🔔 Configure alert channels:")
        print(f"   https://driftassure-frontend-pvoqoo3nx-bilguungzts-projects.vercel.app/alerts")
        print(f"\n{'='*60}\n")
    else:
        print(f"⚠️  Only {success_count} predictions sent. Need at least 30.")
        print(f"   Please check the errors above and try again.")
    
if __name__ == "__main__":
    main()
