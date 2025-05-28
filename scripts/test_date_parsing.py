"""
Test script to validate date parsing functionality
"""
import sys
import os
from datetime import datetime, timedelta
import pytz

# Add scripts directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from tweet_scraper import TweetScraper

def test_date_parsing():
    """Test the date parsing functionality with various formats"""
    
    scraper = TweetScraper()
    
    # Test date strings in various Nitter formats
    test_dates = [
        "May 28, 2025 · 3:45 PM UTC",
        "May 27, 2025 · 15:45 UTC", 
        "3:45 PM · May 27, 2025",
        "15:45 · May 27, 2025",
        "May 27, 2025 at 3:45 PM UTC",
        "May 27, 2025 at 15:45 UTC",
        "2025-05-27 15:45:30 UTC",
        "May 27, 2025",
        "Invalid date format",
        "",
        None
    ]
    
    print("=" * 60)
    print("TESTING DATE PARSING FUNCTIONALITY")
    print("=" * 60)
    
    # Get current date range for comparison
    start_date, end_date = scraper._get_date_range()
    print(f"\nTarget date range:")
    print(f"Start: {start_date}")
    print(f"End:   {end_date}")
    
    print(f"\nTesting date parsing with various formats:")
    print("-" * 60)
    
    for i, date_str in enumerate(test_dates):
        print(f"\nTest {i+1}: '{date_str}'")
        
        try:
            parsed_date = scraper._parse_tweet_date(date_str)
            
            if parsed_date:
                print(f"  SUCCESS: Parsed: {parsed_date}")
                
                # Check if it's in range
                if start_date <= parsed_date <= end_date:
                    print(f"  SUCCESS: Within target range")
                else:
                    print(f"  INFO: Outside target range")
                    
                # Show how many hours ago
                now = datetime.now(pytz.UTC)
                hours_ago = (now - parsed_date).total_seconds() / 3600
                print(f"  INFO: {hours_ago:.1f} hours ago")
                
            else:
                print(f"  FAILED: Could not parse")
                
        except Exception as e:
            print(f"  ERROR: {e}")
    
    print("\n" + "=" * 60)
    print("TESTING WITH MOCK TWEET DATA")
    print("=" * 60)
    
    # Test with mock tweet data that has yesterday's date
    yesterday = datetime.now(pytz.UTC) - timedelta(days=1)
    yesterday_str = yesterday.strftime("%b %d, %Y · %I:%M %p UTC")
    
    mock_tweets_with_dates = [
        {
            "content": "Excited to announce GPT-5 with revolutionary capabilities!",
            "date": yesterday_str,
            "should_include": True
        },
        {
            "content": "Our latest research breakthrough in AI safety.",
            "date": "May 26, 2025 · 2:30 PM UTC",  # Day before yesterday
            "should_include": False
        },
        {
            "content": "Today's announcement about our new partnership.",
            "date": datetime.now(pytz.UTC).strftime("%b %d, %Y · %I:%M %p UTC"),  # Today
            "should_include": False
        }
    ]
    
    print(f"\nMock tweet filtering test:")
    print(f"Target date: {yesterday.strftime('%b %d, %Y')}")
    print("-" * 40)
    
    for i, mock_tweet in enumerate(mock_tweets_with_dates):
        print(f"\nMock Tweet {i+1}:")
        print(f"  Content: {mock_tweet['content'][:50]}...")
        print(f"  Date string: '{mock_tweet['date']}'")
        
        parsed_date = scraper._parse_tweet_date(mock_tweet['date'])
        if parsed_date:
            in_range = start_date <= parsed_date <= end_date
            expected = mock_tweet['should_include']
            
            print(f"  Parsed date: {parsed_date}")
            print(f"  In range: {in_range}")
            print(f"  Expected: {expected}")
            print(f"  Result: {'PASS' if in_range == expected else 'FAIL'}")
        else:
            print(f"  ERROR: Could not parse date")
    
    print("\n" + "=" * 60)
    print("DATE PARSING TEST COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    test_date_parsing()
