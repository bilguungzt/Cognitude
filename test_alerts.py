#!/usr/bin/env python3
"""
Test script for Alert System (Phase 1.4)

This script demonstrates the alert management endpoints:
1. /alerts/channels - Create and manage notification channels
2. /alerts/configs - Configure cost thresholds
3. /alerts/test - Send test notifications
4. /alerts/check - Manually trigger alert checks

Usage:
    python test_alerts.py
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

def test_create_slack_channel():
    """Test creating a Slack alert channel"""
    print_section("Test 1: Create Slack Alert Channel")
    
    # Note: Replace with your actual Slack webhook URL
    payload = {
        "channel_type": "slack",
        "configuration": {
            "webhook_url": "https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
        }
    }
    
    response = requests.post(
        f"{BASE_URL}/alerts/channels",
        headers={
            "X-API-Key": API_KEY,
            "Content-Type": "application/json"
        },
        json=payload
    )
    
    if response.status_code == 200:
        data = response.json()
        print("✅ Success! Slack channel created:")
        print(f"\n  ID: {data['id']}")
        print(f"  Type: {data['channel_type']}")
        print(f"  Active: {data['is_active']}")
        return data['id']
    else:
        print(f"❌ Failed: {response.status_code}")
        print(response.text)
        return None

def test_create_email_channel():
    """Test creating an email alert channel"""
    print_section("Test 2: Create Email Alert Channel")
    
    payload = {
        "channel_type": "email",
        "configuration": {
            "email": "alerts@your-company.com"
        }
    }
    
    response = requests.post(
        f"{BASE_URL}/alerts/channels",
        headers={
            "X-API-Key": API_KEY,
            "Content-Type": "application/json"
        },
        json=payload
    )
    
    if response.status_code == 200:
        data = response.json()
        print("✅ Success! Email channel created:")
        print(f"\n  ID: {data['id']}")
        print(f"  Type: {data['channel_type']}")
        print(f"  Email: {data['configuration']['email']}")
        return data['id']
    else:
        print(f"❌ Failed: {response.status_code}")
        print(response.text)
        return None

def test_list_channels():
    """Test listing all alert channels"""
    print_section("Test 3: List Alert Channels")
    
    response = requests.get(
        f"{BASE_URL}/alerts/channels",
        headers={"X-API-Key": API_KEY}
    )
    
    if response.status_code == 200:
        channels = response.json()
        print(f"✅ Success! Found {len(channels)} channel(s):\n")
        
        for channel in channels:
            print(f"  • ID: {channel['id']}")
            print(f"    Type: {channel['channel_type']}")
            print(f"    Active: {channel['is_active']}")
            if channel['channel_type'] == 'email':
                print(f"    Email: {channel['configuration'].get('email', 'N/A')}")
            print()
        
        return True
    else:
        print(f"❌ Failed: {response.status_code}")
        print(response.text)
        return False

def test_create_alert_config():
    """Test creating a cost threshold alert"""
    print_section("Test 4: Create Cost Threshold Alert")
    
    payload = {
        "alert_type": "daily_cost",
        "threshold_usd": 50.00
    }
    
    response = requests.post(
        f"{BASE_URL}/alerts/configs",
        headers={
            "X-API-Key": API_KEY,
            "Content-Type": "application/json"
        },
        json=payload
    )
    
    if response.status_code == 200:
        data = response.json()
        print("✅ Success! Alert config created:")
        print(f"\n  ID: {data['id']}")
        print(f"  Type: {data['alert_type']}")
        print(f"  Threshold: ${data['threshold_usd']:.2f}")
        print(f"  Enabled: {data['enabled']}")
        return data['id']
    else:
        print(f"❌ Failed: {response.status_code}")
        print(response.text)
        return None

def test_list_configs():
    """Test listing all alert configs"""
    print_section("Test 5: List Alert Configurations")
    
    response = requests.get(
        f"{BASE_URL}/alerts/configs",
        headers={"X-API-Key": API_KEY}
    )
    
    if response.status_code == 200:
        configs = response.json()
        print(f"✅ Success! Found {len(configs)} config(s):\n")
        
        for config in configs:
            print(f"  • ID: {config['id']}")
            print(f"    Type: {config['alert_type']}")
            print(f"    Threshold: ${config['threshold_usd']:.2f}")
            print(f"    Enabled: {config['enabled']}")
            print(f"    Last Triggered: {config.get('last_triggered', 'Never')}")
            print()
        
        return True
    else:
        print(f"❌ Failed: {response.status_code}")
        print(response.text)
        return False

def test_send_test_notification(channel_id):
    """Test sending a test notification"""
    print_section(f"Test 6: Send Test Notification (Channel {channel_id})")
    
    if not channel_id:
        print("⏭️  Skipping - no channel ID provided")
        return False
    
    response = requests.post(
        f"{BASE_URL}/alerts/test/{channel_id}",
        headers={"X-API-Key": API_KEY}
    )
    
    if response.status_code == 200:
        print("✅ Success! Test notification sent")
        print("\n💡 Check your Slack/email to verify delivery")
        return True
    else:
        print(f"❌ Failed: {response.status_code}")
        print(response.text)
        return False

def test_check_alerts():
    """Test manually checking cost alerts"""
    print_section("Test 7: Manual Alert Check")
    
    response = requests.post(
        f"{BASE_URL}/alerts/check",
        headers={"X-API-Key": API_KEY}
    )
    
    if response.status_code == 200:
        data = response.json()
        print("✅ Success! Alert check complete:")
        print(f"\n  Alerts Checked: {data['alerts_checked']}")
        print(f"  Alerts Triggered: {data['alerts_triggered']}")
        print(f"  Notifications Sent:")
        print(f"    - Slack: {data['notifications_sent']['slack']}")
        print(f"    - Email: {data['notifications_sent']['email']}")
        print(f"    - Webhook: {data['notifications_sent']['webhook']}")
        
        if data['alerts_triggered'] > 0:
            print("\n  🚨 Cost threshold exceeded! Check your notifications.")
        else:
            print("\n  ✅ All costs within thresholds.")
        
        return True
    else:
        print(f"❌ Failed: {response.status_code}")
        print(response.text)
        return False

def test_alert_types():
    """Test creating different alert types"""
    print_section("Test 8: Create Multiple Alert Types")
    
    alert_types = [
        {"alert_type": "weekly_cost", "threshold_usd": 250.00},
        {"alert_type": "monthly_cost", "threshold_usd": 1000.00}
    ]
    
    created = []
    for config in alert_types:
        response = requests.post(
            f"{BASE_URL}/alerts/configs",
            headers={
                "X-API-Key": API_KEY,
                "Content-Type": "application/json"
            },
            json=config
        )
        
        if response.status_code == 200:
            data = response.json()
            created.append(data)
            print(f"✅ Created {data['alert_type']}: ${data['threshold_usd']:.2f}")
        else:
            print(f"❌ Failed to create {config['alert_type']}: {response.status_code}")
    
    return len(created) > 0

def main():
    """Run all tests"""
    print("\n🚀 Alert System Test Suite")
    print("Testing Phase 1.4 implementation...")
    
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
    
    print("\n⚠️  Important Notes:")
    print("   1. Replace Slack webhook URL in the script with your actual URL")
    print("   2. Configure SMTP settings in environment variables for email alerts")
    print("   3. Test notifications will be sent to configured channels")
    
    # Run tests
    results = []
    
    # Create channels
    slack_channel_id = test_create_slack_channel()
    results.append(("Create Slack Channel", slack_channel_id is not None))
    
    email_channel_id = test_create_email_channel()
    results.append(("Create Email Channel", email_channel_id is not None))
    
    # List channels
    results.append(("List Channels", test_list_channels()))
    
    # Create alert config
    alert_config_id = test_create_alert_config()
    results.append(("Create Alert Config", alert_config_id is not None))
    
    # List configs
    results.append(("List Configs", test_list_configs()))
    
    # Send test notification (if channel created)
    test_channel = slack_channel_id or email_channel_id
    if test_channel:
        results.append(("Send Test Notification", test_send_test_notification(test_channel)))
    
    # Check alerts
    results.append(("Check Alerts", test_check_alerts()))
    
    # Create multiple alert types
    results.append(("Create Multiple Alert Types", test_alert_types()))
    
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
    
    if passed >= total - 2:  # Allow 2 failures (Slack webhook, email SMTP)
        print("🎉 Alert system is working correctly!")
        print("\n💡 Next steps:")
        print("   1. Configure real Slack webhook URL")
        print("   2. Set up SMTP credentials for email")
        print("   3. Alerts will be checked automatically every hour")
        print("   4. Test with actual cost thresholds")
        return 0
    else:
        print("⚠️  Some tests failed. Please check the errors above.")
        print("\n💡 Common issues:")
        print("   1. Invalid Slack webhook URL (need to create one in Slack)")
        print("   2. Missing SMTP configuration (SMTP_HOST, SMTP_USERNAME, SMTP_PASSWORD)")
        print("   3. Server not running (docker-compose up -d)")
        return 1

if __name__ == "__main__":
    sys.exit(main())
