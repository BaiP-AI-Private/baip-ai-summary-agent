#!/usr/bin/env python3
"""
Simple test without unicode characters
"""

import asyncio
import os
import sys
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv

# Add the scripts directory to the path
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'scripts'))

from twitter_scraper_scrapfly import TwitterScraperNew

async def simple_test():
    """Simple test with basic output"""
    load_dotenv()
    load_dotenv(dotenv_path='../.env')
    
    print("=" * 50)
    print("SCRAPING TEST")
    print("=" * 50)
    
    # Check environment
    scrapfly_key = os.getenv("SCRAPFLY_API_KEY")
    print(f"Scrapfly API Key: {'Present' if scrapfly_key else 'Missing'}")
    
    # Test date logic
    utc = timezone.utc
    now = datetime.now(utc)
    cutoff_72h = now - timedelta(hours=72)
    
    print(f"Current time (UTC): {now}")
    print(f"Looking for tweets since: {cutoff_72h}")
    
    # Test one account
    try:
        async with TwitterScraperNew() as scraper:
            print("\nTesting OpenAI account...")
            
            tweets = await scraper.scrape_user_timeline("OpenAI", max_tweets=5)
            print(f"Raw tweets found: {len(tweets)}")
            
            if tweets:
                print("\nSample tweets:")
                for i, tweet in enumerate(tweets[:3]):
                    created_at = tweet.get("created_at", "No date")
                    text = tweet.get("text", "No text")[:80] + "..."
                    
                    try:
                        if created_at != "No date":
                            tweet_date = datetime.strptime(created_at, "%a %b %d %H:%M:%S %z %Y")
                            hours_ago = (now - tweet_date).total_seconds() / 3600
                            is_recent = scraper.is_tweet_recent(tweet)
                            print(f"  {i+1}. {hours_ago:.1f}h ago - Recent: {is_recent}")
                            print(f"     {text}")
                        else:
                            print(f"  {i+1}. No date - {text}")
                    except Exception as e:
                        print(f"  {i+1}. Date error: {e}")
                
                recent_tweets = [t for t in tweets if scraper.is_tweet_recent(t)]
                print(f"\nRecent tweets: {len(recent_tweets)}")
            else:
                print("No tweets found - scraping may be blocked")
                
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(simple_test())
