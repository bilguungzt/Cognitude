import requests
import time
import uuid
from datetime import datetime, timezone

API_BASE_URL = "http://localhost:8000"

def test_drift_detection_e2e():
    try:
        # a. Register a new organization with unique name
        org_name = f"Drift Test Inc. {uuid.uuid4().hex[:8]}"
        print(f"Registering organization: {org_name}")
        response = requests.post(
            f"{API_BASE_URL}/auth/register",
            json={"name": org_name}
        )
        response.raise_for_status()
        org_data = response.json()
        
        # b. Store the new `api_key`
        api_key = org_data["api_key"]
        headers = {"X-API-Key": api_key}
        print(f"Organization registered with API key: {api_key[:10]}...")
        
        # c. Register a new model "Drift Test Model" using that API key
        print("Creating model...")
        model_response = requests.post(
            f"{API_BASE_URL}/models/",
            headers=headers,
            json={
                "name": "Drift Test Model",
                "version": "1.0",
                "description": "A model for drift testing",
                "features": [
                    {"feature_name": "feature1", "feature_type": "numeric", "order": 1}
                ]
            }
        )
        model_response.raise_for_status()
        model_data = model_response.json()
        print(f"Model data: {model_data}")
        
        # d. Store the new `model_id`
        model_id = model_data["id"]
        print(f"Model created with ID: {model_id}")
        
        # e. Log 50 "baseline" predictions (prediction_value = 0.5)
        print("Logging baseline predictions...")
        baseline_samples = [0.5] * 50  # Store samples for baseline_stats
        for i in range(50):
            timestamp = datetime.now(timezone.utc).isoformat()
            pred_response = requests.post(
                f"{API_BASE_URL}/predictions/models/{model_id}/predictions",
                headers=headers,
                json=[{
                    "features": {"feature1": 1.0},
                    "prediction_value": 0.5,
                    "timestamp": timestamp
                }]
            )
            pred_response.raise_for_status()
            time.sleep(0.01)  # Small delay to ensure unique timestamps
        
        # Update model with baseline_stats
        print("Updating model with baseline stats...")
        feature_id = model_data["features"][0]["id"]
        update_response = requests.put(
            f"{API_BASE_URL}/models/{model_id}/features/{feature_id}",
            headers=headers,
            json={
                "baseline_stats": {
                    "samples": baseline_samples
                }
            }
        )
        update_response.raise_for_status()
        
        # Small delay to ensure timestamp differences
        time.sleep(1)
        
        # f. Log 50 "drifted" predictions (prediction_value = 0.9)
        print("Logging drifted predictions...")
        for i in range(50):
            timestamp = datetime.now(timezone.utc).isoformat()
            pred_response = requests.post(
                f"{API_BASE_URL}/predictions/models/{model_id}/predictions",
                headers=headers,
                json=[{
                    "features": {"feature1": 1.0},
                    "prediction_value": 0.9,
                    "timestamp": timestamp
                }]
            )
            pred_response.raise_for_status()
            time.sleep(0.01)  # Small delay to ensure unique timestamps
        
        # g. Call the GET /drift/models/{model_id}/drift/current endpoint
        print("Checking for drift...")
        drift_response = requests.get(
            f"{API_BASE_URL}/drift/models/{model_id}/drift/current",
            headers=headers
        )
        drift_response.raise_for_status()
        drift_data = drift_response.json()
        
        # h. Check the JSON response. It MUST assert that `drift_detected` is `True`
        assert drift_data["drift_detected"] == True, f"Expected drift_detected=True, got {drift_data['drift_detected']}"
        print(f"Drift detection successful. Drift score: {drift_data['drift_score']}")
        
        # i. If all steps pass, print success message
        print("✅ Drift Detection E2E Test PASSED!")
        
    except Exception as e:
        # j. If any step fails, print the error and exit
        print(f"❌ Drift Detection E2E Test FAILED: {str(e)}")
        exit(1)

if __name__ == "__main__":
    test_drift_detection_e2e()
