import os
import requests
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()

def test_slack_webhook():
    """Test Slack webhook to ensure it's working"""
    webhook_url = os.getenv("SLACK_WEBHOOK_URL")
    if not webhook_url:
        print("ERROR: SLACK_WEBHOOK_URL not found in environment variables")
        return False

    test_message = {
        "text": f"Test Message - {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}\n\nThis is a test message to verify the Slack webhook is working correctly.",
        "mrkdwn": True
    }

    try:
        response = requests.post(
            webhook_url,
            json=test_message,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code == 200:
            print("SUCCESS: Slack webhook test successful!")
            print(f"Response: {response.text}")
            return True
        else:
            print(f"ERROR: Slack webhook failed with status {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"ERROR: Testing Slack webhook failed: {e}")
        return False

if __name__ == "__main__":
    test_slack_webhook()
