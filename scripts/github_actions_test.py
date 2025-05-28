#!/usr/bin/env python3
"""
Simplified tweet scraper for GitHub Actions debugging
"""
import os
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_environment():
    """Test environment setup in GitHub Actions"""
    logger.info("=" * 50)
    logger.info("GITHUB ACTIONS ENVIRONMENT TEST")
    logger.info("=" * 50)
    
    # Check environment variables
    api_key = os.getenv("OPENAI_API_KEY")
    slack_url = os.getenv("SLACK_WEBHOOK_URL")
    
    logger.info(f"OpenAI API key present: {bool(api_key)}")
    logger.info(f"Slack webhook URL present: {bool(slack_url)}")
    logger.info(f"Current working directory: {os.getcwd()}")
    
    if not api_key:
        logger.error("OPENAI_API_KEY not found in environment")
        return False
        
    if not slack_url:
        logger.error("SLACK_WEBHOOK_URL not found in environment")
        return False
    
    return True

def test_openai():
    """Test OpenAI library initialization"""
    logger.info("Testing OpenAI library...")
    
    api_key = os.getenv("OPENAI_API_KEY")
    
    try:
        # Method 1: New OpenAI client (v1.0+)
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        logger.info("✅ New OpenAI client initialized successfully")
        return client, "new"
        
    except Exception as e:
        logger.warning(f"New OpenAI client failed: {e}")
        
        try:
            # Method 2: Legacy OpenAI API (v0.x)
            import openai
            openai.api_key = api_key
            logger.info("✅ Legacy OpenAI API configured successfully")
            return None, "legacy"
            
        except Exception as e2:
            logger.error(f"Legacy OpenAI also failed: {e2}")
            return None, None

def test_slack():
    """Test Slack webhook"""
    import requests
    
    webhook_url = os.getenv("SLACK_WEBHOOK_URL")
    if not webhook_url:
        logger.error("No Slack webhook URL available")
        return False
    
    test_message = {
        "text": f"🧪 GitHub Actions Test - {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}",
        "mrkdwn": True
    }
    
    try:
        response = requests.post(webhook_url, json=test_message, timeout=30)
        if response.status_code == 200:
            logger.info("✅ Slack test message sent successfully")
            return True
        else:
            logger.error(f"Slack test failed: {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"Slack test error: {e}")
        return False

def main():
    """Main test function"""
    logger.info("Starting GitHub Actions compatibility test...")
    
    # Test 1: Environment
    if not test_environment():
        logger.error("Environment test failed")
        return
    
    # Test 2: OpenAI
    client, method = test_openai()
    if method is None:
        logger.error("OpenAI test failed")
        return
    
    # Test 3: Slack
    if not test_slack():
        logger.error("Slack test failed")
        return
    
    logger.info("=" * 50)
    logger.info("ALL TESTS PASSED - GITHUB ACTIONS COMPATIBLE")
    logger.info("=" * 50)

if __name__ == "__main__":
    main()
