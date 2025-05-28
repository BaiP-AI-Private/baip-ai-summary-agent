"""
Debug script for GitHub Actions to test OpenAI client initialization
"""
import os
import sys
from dotenv import load_dotenv

print("=" * 50)
print("GITHUB ACTIONS DEBUG SCRIPT")
print("=" * 50)

# Load environment variables
load_dotenv()
print(f"Current working directory: {os.getcwd()}")
print(f"Python version: {sys.version}")

# Check environment variables
api_key = os.getenv("OPENAI_API_KEY")
slack_url = os.getenv("SLACK_WEBHOOK_URL")

print(f"OpenAI API key present: {bool(api_key)}")
print(f"Slack webhook URL present: {bool(slack_url)}")

if api_key:
    print(f"API key starts with: {api_key[:10]}...")
else:
    print("API key is None or empty")

# Test OpenAI import and initialization
print("\nTesting OpenAI library...")
try:
    from openai import OpenAI
    print("✅ OpenAI import successful")
    
    if api_key:
        print("Testing OpenAI client initialization...")
        client = OpenAI(api_key=api_key)
        print("✅ OpenAI client initialized successfully")
        
        # Test a simple API call
        print("Testing simple API call...")
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Hello, respond with 'API test successful'"}],
            max_tokens=10
        )
        print(f"✅ API test successful: {response.choices[0].message.content}")
        
    else:
        print("❌ No API key available for testing")
        
except Exception as e:
    print(f"❌ Error with OpenAI: {e}")
    print(f"Error type: {type(e)}")
    
    # Try legacy approach
    print("\nTrying legacy OpenAI initialization...")
    try:
        import openai
        openai.api_key = api_key
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Hello"}],
            max_tokens=10
        )
        print("✅ Legacy OpenAI API works")
    except Exception as e2:
        print(f"❌ Legacy OpenAI also failed: {e2}")

print("\nEnvironment check complete!")
