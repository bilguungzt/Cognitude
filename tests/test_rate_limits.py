import requests
import time

# --- Configuration ---
BASE_URL = "http://127.0.0.1:8000"
# This is a placeholder key. Replace with a valid key from your system.
# You can generate one by running: python scripts/create_org_and_print_key.py "Test Org"
API_KEY = "YOUR_API_KEY"
# The chat completions endpoint is rate-limited
ENDPOINT = "/v1/chat/completions"

# --- Test Parameters ---
# The default rate limit is 5 requests per second.
# We will send 10 requests to ensure the limit is triggered.
REQUESTS_TO_SEND = 10

def test_rate_limiting():
    """
    Sends rapid requests to a rate-limited endpoint to verify that
    a 429 Too Many Requests error is returned when the limit is exceeded.
    """
    if API_KEY == "YOUR_API_KEY":
        print("� ERROR: Please replace 'YOUR_API_KEY' with a valid API key.")
        print("You can generate one by running: python scripts/create_org_and_print_key.py \"Test Org\"")
        return

    headers = {
        "X-API-Key": API_KEY,
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "gpt-3.5-turbo",
        "messages": [{"role": "user", "content": "This is a test."}]
    }

    print(f"� Sending {REQUESTS_TO_SEND} requests to {ENDPOINT}...")

    rate_limit_hit = False
    for i in range(REQUESTS_TO_SEND):
        try:
            response = requests.post(f"{BASE_URL}{ENDPOINT}", headers=headers, json=payload)
            print(f"Request {i+1}: Status Code {response.status_code}")
            
            if response.status_code == 429:
                rate_limit_hit = True
                print("✅ SUCCESS: Rate limit exceeded as expected (HTTP 429).")
                break
        except requests.exceptions.ConnectionError as e:
            print(f"🔴 ERROR: Connection failed. Is the server running at {BASE_URL}?")
            print(e)
            return

    print("\n--- Test Summary ---")
    if not rate_limit_hit:
        print("❌ FAILED: The rate limit was not triggered.")
        print("Check the rate limit configuration in 'app/limiter.py' and ensure the server is running.")
    else:
        print("✅ PASSED: Rate limit test completed successfully.")

if __name__ == "__main__":
    test_rate_limiting()
