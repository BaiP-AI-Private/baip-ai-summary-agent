"""
Test script to simulate a working Nitter instance and test complete tweet filtering
"""
import sys
import os
from datetime import datetime, timedelta
import pytz
from unittest.mock import Mock, patch
from bs4 import BeautifulSoup

# Add scripts directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from tweet_scraper import TweetScraper

def create_mock_nitter_html():
    """Create mock HTML that looks like a Nitter page with tweets from different dates"""
    
    # Create dates for testing
    yesterday = datetime.now(pytz.UTC) - timedelta(days=1)
    today = datetime.now(pytz.UTC)
    day_before_yesterday = datetime.now(pytz.UTC) - timedelta(days=2)
    
    # Format dates in Nitter style
    yesterday_str = yesterday.strftime("%b %d, %Y · %I:%M %p UTC")
    today_str = today.strftime("%b %d, %Y · %I:%M %p UTC")
    old_str = day_before_yesterday.strftime("%b %d, %Y · %I:%M %p UTC")
    
    mock_html = f"""
    <html>
    <head><title>OpenAI (@openai) / Twitter</title></head>
    <body>
        <div class="timeline">
            <!-- Tweet from yesterday (should be included) -->
            <div class="timeline-item">
                <div class="tweet">
                    <div class="tweet-header">
                        <span class="tweet-date">
                            <a href="/openai/status/1" title="{yesterday_str}">
                                {yesterday.strftime("%I:%M %p · %b %d, %Y")}
                            </a>
                        </span>
                    </div>
                    <div class="tweet-content">
                        <div class="tweet-body">
                            🚀 Excited to announce GPT-5 with revolutionary reasoning capabilities! 
                            Our latest breakthrough in AI research is now available to developers.
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Tweet from today (should be excluded) -->
            <div class="timeline-item">
                <div class="tweet">
                    <div class="tweet-header">
                        <span class="tweet-date">
                            <a href="/openai/status/2" title="{today_str}">
                                {today.strftime("%I:%M %p · %b %d, %Y")}
                            </a>
                        </span>
                    </div>
                    <div class="tweet-content">
                        <div class="tweet-body">
                            Today's update: We're improving our safety measures and working on new features.
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Another tweet from yesterday (should be included) -->
            <div class="timeline-item">
                <div class="tweet">
                    <div class="tweet-header">
                        <span class="tweet-date">
                            <a href="/openai/status/3" title="{yesterday_str.replace('05:', '02:')}">
                                {yesterday.replace(hour=14).strftime("%I:%M %p · %b %d, %Y")}
                            </a>
                        </span>
                    </div>
                    <div class="tweet-content">
                        <div class="tweet-body">
                            Our partnership with leading universities is accelerating AI research. 
                            New collaborative projects launching soon! 🎓
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Tweet from day before yesterday (should be excluded) -->
            <div class="timeline-item">
                <div class="tweet">
                    <div class="tweet-header">
                        <span class="tweet-date">
                            <a href="/openai/status/4" title="{old_str}">
                                {day_before_yesterday.strftime("%I:%M %p · %b %d, %Y")}
                            </a>
                        </span>
                    </div>
                    <div class="tweet-content">
                        <div class="tweet-body">
                            Old tweet from two days ago that should not be included in yesterday's summary.
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Tweet with no date (should be included as fallback) -->
            <div class="timeline-item">
                <div class="tweet">
                    <div class="tweet-content">
                        <div class="tweet-body">
                            Tweet with missing date information - should be included as fallback.
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    
    return mock_html

def test_complete_tweet_filtering():
    """Test the complete tweet filtering process with mock data"""
    
    print("=" * 70)
    print("TESTING COMPLETE TWEET FILTERING WITH MOCK NITTER DATA")
    print("=" * 70)
    
    # Create a scraper instance
    scraper = TweetScraper()
    
    # Get the date range we're targeting
    start_date, end_date = scraper._get_date_range()
    
    print(f"\nTarget date range:")
    print(f"Start: {start_date}")
    print(f"End:   {end_date}")
    print(f"Target day: {start_date.strftime('%b %d, %Y')}")
    
    # Create mock HTML
    mock_html = create_mock_nitter_html()
    
    # Mock the session.get method to return our mock HTML
    with patch.object(scraper.session, 'get') as mock_get:
        # Configure the mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = mock_html
        mock_get.return_value = mock_response
        
        # Set up a mock working instance
        scraper.current_instance = "https://mock-nitter.example.com"
        scraper.current_source_type = "nitter"
        
        print(f"\nTesting tweet extraction for @openai...")
        print(f"Mock instance: {scraper.current_instance}")
        
        # Test the get_user_tweets method
        tweets = scraper.get_user_tweets("openai", start_date, end_date)
        
        print(f"\nResults:")
        print(f"Total tweets found: {len(tweets)}")
        print(f"Expected: 3 tweets (2 from yesterday + 1 fallback with no date)")
        
        print(f"\nExtracted tweets:")
        for i, tweet in enumerate(tweets):
            print(f"  {i+1}. {tweet}")
        
        # Analyze results
        expected_keywords = [
            "GPT-5",  # From yesterday's tweet
            "partnership",  # From yesterday's tweet
            "missing date"  # From fallback tweet
        ]
        
        unexpected_keywords = [
            "Today's update",  # From today (should be excluded)
            "Old tweet"  # From day before yesterday (should be excluded)
        ]
        
        print(f"\nAnalysis:")
        
        all_text = " ".join(tweets).lower()
        
        for keyword in expected_keywords:
            if keyword.lower() in all_text:
                print(f"  ✅ Found expected content: '{keyword}'")
            else:
                print(f"  ❌ Missing expected content: '{keyword}'")
        
        for keyword in unexpected_keywords:
            if keyword.lower() in all_text:
                print(f"  ❌ Found unexpected content: '{keyword}' (should be filtered out)")
            else:
                print(f"  ✅ Correctly filtered out: '{keyword}'")
        
        # Test if filtering worked correctly
        success = (
            len(tweets) == 3 and  # Should have 3 tweets
            "gpt-5" in all_text and  # Should include yesterday's GPT-5 tweet
            "partnership" in all_text and  # Should include yesterday's partnership tweet
            "missing date" in all_text and  # Should include fallback tweet
            "today's update" not in all_text and  # Should exclude today's tweet
            "old tweet" not in all_text  # Should exclude old tweet
        )
        
        print(f"\nOverall Result: {'PASS' if success else 'FAIL'}")
        
        if success:
            print("   Date filtering is working correctly!")
            print("   - Includes tweets from target date (yesterday)")
            print("   - Excludes tweets from other dates")
            print("   - Includes tweets with missing dates as fallback")
        else:
            print("   Date filtering needs adjustment")
    
    print("\n" + "=" * 70)
    print("COMPLETE TWEET FILTERING TEST FINISHED")
    print("=" * 70)

if __name__ == "__main__":
    test_complete_tweet_filtering()
