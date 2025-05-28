import os
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv(dotenv_path='../.env')

def test_openai_api():
    """Test OpenAI API to ensure it's working"""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("ERROR: OPENAI_API_KEY not found in environment variables")
        return False

    try:
        client = OpenAI(api_key=api_key)
        
        # Simple test prompt
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Hello! This is a test. Please respond with 'API test successful'."}],
            temperature=0.0,
            max_tokens=10
        )
        
        result = response.choices[0].message.content.strip()
        print(f"SUCCESS: OpenAI API test successful!")
        print(f"Response: {result}")
        return True
        
    except Exception as e:
        print(f"ERROR: OpenAI API test failed: {e}")
        return False

if __name__ == "__main__":
    test_openai_api()
