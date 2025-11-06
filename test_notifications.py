"""Test script to verify notification system is working."""
import requests
import time
from datetime import datetime, timezone

API_BASE_URL = "http://localhost:8000"

def test_notification_system():
    print("=" * 60)
    print("Testing DriftGuard Notification System")
    print("=" * 60)
    
    # 1. Register organization
    print("\n1. Registering organization...")
    response = requests.post(
        f"{API_BASE_URL}/auth/register",
        json={"name": f"Test Notifications {int(time.time())}"}
    )
    response.raise_for_status()
    org_data = response.json()
    api_key = org_data["api_key"]
    headers = {"X-API-Key": api_key}
    print(f"   ✅ Organization created with API key: {api_key[:10]}...")
    
    # 2. Create model
    print("\n2. Creating model...")
    response = requests.post(
        f"{API_BASE_URL}/models/",
        headers=headers,
        json={
            "name": "Notification Test Model",
            "version": "1.0",
            "description": "Testing notifications",
            "features": [
                {"feature_name": "feature1", "feature_type": "numeric", "order": 1}
            ]
        }
    )
    response.raise_for_status()
    model_data = response.json()
    model_id = model_data["id"]
    feature_id = model_data["features"][0]["id"]
    print(f"   ✅ Model created with ID: {model_id}")
    
    # 3. Configure alert channels
    print("\n3. Configuring alert channels...")
    
    # Email channel
    print("   Adding email channel...")
    response = requests.post(
        f"{API_BASE_URL}/alert-channels/",
        headers=headers,
        json={
            "channel_type": "email",
            "configuration": {"email": "test@example.com"}
        }
    )
    response.raise_for_status()
    email_channel = response.json()
    print(f"   ✅ Email channel created (ID: {email_channel['id']})")
    
    # Slack channel (optional)
    print("   Adding Slack channel...")
    response = requests.post(
        f"{API_BASE_URL}/alert-channels/",
        headers=headers,
        json={
            "channel_type": "slack",
            "configuration": {"webhook_url": "https://hooks.slack.com/test"}
        }
    )
    response.raise_for_status()
    slack_channel = response.json()
    print(f"   ✅ Slack channel created (ID: {slack_channel['id']})")
    
    # List channels
    print("\n   Listing alert channels...")
    response = requests.get(f"{API_BASE_URL}/alert-channels/", headers=headers)
    response.raise_for_status()
    channels = response.json()
    print(f"   ✅ Found {len(channels)} alert channels")
    for channel in channels:
        print(f"      - {channel['channel_type']}: Active={channel['is_active']}")
    
    # 4. Log baseline predictions
    print("\n4. Logging baseline predictions...")
    baseline_samples = []
    for i in range(50):
        value = 0.5
        baseline_samples.append(value)
        response = requests.post(
            f"{API_BASE_URL}/predictions/models/{model_id}/predictions",
            headers=headers,
            json=[{
                "features": {"feature1": 1.0},
                "prediction_value": value,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }]
        )
        response.raise_for_status()
        time.sleep(0.01)
    print(f"   ✅ Logged {len(baseline_samples)} baseline predictions")
    
    # 5. Update model with baseline stats
    print("\n5. Updating model with baseline statistics...")
    response = requests.put(
        f"{API_BASE_URL}/models/{model_id}/features/{feature_id}",
        headers=headers,
        json={"baseline_stats": {"samples": baseline_samples}}
    )
    response.raise_for_status()
    print("   ✅ Baseline statistics updated")
    
    # 6. Log drifted predictions
    print("\n6. Logging drifted predictions to trigger alert...")
    for i in range(50):
        response = requests.post(
            f"{API_BASE_URL}/predictions/models/{model_id}/predictions",
            headers=headers,
            json=[{
                "features": {"feature1": 1.0},
                "prediction_value": 0.9,  # Significantly different!
                "timestamp": datetime.now(timezone.utc).isoformat()
            }]
        )
        response.raise_for_status()
        time.sleep(0.01)
    print("   ✅ Logged 50 drifted predictions")
    
    # 7. Check for drift (should trigger notifications)
    print("\n7. Checking drift status...")
    response = requests.get(
        f"{API_BASE_URL}/drift/models/{model_id}/drift/current",
        headers=headers
    )
    response.raise_for_status()
    drift_data = response.json()
    
    print(f"   Drift Detected: {drift_data['drift_detected']}")
    print(f"   Drift Score: {drift_data['drift_score']:.3f}")
    print(f"   P-Value: {drift_data['p_value']:.4f}")
    print(f"   Samples: {drift_data['samples']}")
    
    if drift_data['drift_detected']:
        print("\n   ✅ DRIFT DETECTED! Notifications should be sent.")
        print("   📧 Check console output for '[DEV MODE]' email notification")
        print("   📱 Check console output for Slack notification attempt")
    else:
        print("\n   ⚠️  No drift detected (may need more data difference)")
    
    # 8. Check Docker logs for notification attempts
    print("\n8. To see notification logs, run:")
    print("   docker logs driftguard_mvp-api-1 --tail 50 | grep -i 'email\\|slack\\|alert'")
    
    print("\n" + "=" * 60)
    print("✅ Notification system test complete!")
    print("=" * 60)

if __name__ == "__main__":
    try:
        test_notification_system()
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
