#!/usr/bin/env python3
"""
Quick test to check if the scraper can find tweets
"""

import asyncio
import os
import sys
from dotenv import load_dotenv

# Add the scripts directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from twitter_scraper_scrapfly import TwitterScraperNew

async def test_scraping():
    """Test if we can find any tweets"""
    load_dotenv()
    load_dotenv(dotenv_path='../.env')
    
    # Test with just one account
    test_account = "OpenAI"
    
    try:
        async with TwitterScraperNew() as scraper:
            print(f"Testing scraping for @{test_account}...")
            tweets = await scraper.scrape_user_timeline(test_account, max_tweets=5)
            
            print(f"Found {len(tweets)} tweets")
            
            if tweets:
                print("\nSample tweets:")
                for i, tweet in enumerate(tweets[:3]):
                    text = tweet.get('text', 'No text')[:100]
                    created = tweet.get('created_at', 'No date')
                    likes = tweet.get('favorite_count', 0)
                    print(f"{i+1}. {text}... ({created}) - {likes} likes")
                    
                # Check if any are from yesterday
                yesterday_tweets = [t for t in tweets if scraper.is_tweet_from_yesterday(t)]
                print(f"\nTweets from yesterday: {len(yesterday_tweets)}")
                
            else:
                print("No tweets found - this indicates the scraping is not working")
                
    except Exception as e:
        print(f"Error during testing: {e}")

if __name__ == "__main__":
    asyncio.run(test_scraping())
