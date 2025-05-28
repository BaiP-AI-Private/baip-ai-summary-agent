"""
Test script to validate the tweet scraper functionality with mock data
"""
import os
import sys
from dotenv import load_dotenv
import logging

# Add current directory to path so we can import the scraper
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from tweet_scraper import TweetScraper

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_with_mock_data():
    """Test the scraper with mock tweet data"""
    # Load environment variables from parent directory
    load_dotenv(dotenv_path='../.env')
    
    # Create scraper instance
    scraper = TweetScraper()
    
    # Mock tweet data simulating what we'd get from actual scraping
    mock_tweets = [
        "@OpenAI: Excited to announce GPT-4 Turbo with improved performance and lower costs for developers!",
        "@AnthropicAI: Claude 3.5 Sonnet now available with enhanced reasoning capabilities and safety features.",
        "@GoogleDeepMind: Breakthrough in multimodal AI - our new Gemini model can understand images, text, and code simultaneously.",
        "@MistralAI: Mistral Large 2 released with 128k context window and improved mathematical reasoning.",
        "@AIatMeta: Llama 3 now powers over 1000 enterprise applications. Open source AI is transforming businesses.",
        "@Cohere: New Command R+ model shows state-of-the-art performance on RAG tasks and tool use.",
        "@perplexity_ai: Our new Pro Search delivers more accurate answers with real-time web data integration.",
        "@scale_ai: Partnership with enterprise clients growing 300% year over year for AI data solutions.",
        "@runwayml: Gen-3 Alpha video generation model now available - creating Hollywood-quality videos from text.",
        "@dair_ai: New research on AI alignment published - making models more helpful, harmless, and honest."
    ]
    
    print("=" * 60)
    print("Testing Tweet Scraper with Mock Data")
    print("=" * 60)
    
    # Test summary generation
    print("\n1. Testing AI Summary Generation...")
    try:
        ai_summary = scraper.generate_summary(mock_tweets)
        print("AI Summary Result:")
        print(ai_summary)
        print("\nAI summary test: PASSED" if ai_summary and "Failed" not in ai_summary else "AI summary test: FAILED (using fallback)")
    except Exception as e:
        print(f"AI summary test: FAILED - {e}")
    
    # Test manual summary generation (fallback)
    print("\n" + "="*60)
    print("\n2. Testing Manual Summary Generation (Fallback)...")
    try:
        manual_summary = scraper.generate_manual_summary(mock_tweets)
        print("Manual Summary Result:")
        print(manual_summary)
        print("\nManual summary test: PASSED" if manual_summary else "Manual summary test: FAILED")
    except Exception as e:
        print(f"Manual summary test: FAILED - {e}")
    
    # Test demo summary
    print("\n" + "="*60)
    print("\n3. Testing Demo Summary Generation...")
    try:
        demo_summary = scraper.generate_demo_summary()
        print("Demo Summary Result:")
        print(demo_summary)
        print("\nDemo summary test: PASSED" if demo_summary else "Demo summary test: FAILED")
    except Exception as e:
        print(f"Demo summary test: FAILED - {e}")
    
    # Test Slack integration
    print("\n" + "="*60)
    print("\n4. Testing Slack Integration...")
    try:
        test_message = f"🧪 **Test Summary** - Mock Data Validation\n\n{manual_summary}\n\n_This is a test message to validate the scraper functionality._"
        slack_result = scraper.send_to_slack(test_message)
        print(f"Slack integration test: {'PASSED' if slack_result else 'FAILED'}")
    except Exception as e:
        print(f"Slack integration test: FAILED - {e}")
    
    print("\n" + "="*60)
    print("Test Summary Complete!")
    print("="*60)

if __name__ == "__main__":
    test_with_mock_data()
