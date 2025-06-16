#!/usr/bin/env python3
"""
Simple debug test for the Twitter scraper (no emojis for Windows compatibility)
"""

import asyncio
import os
import sys
import json
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv

# Add the scripts directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from twitter_scraper_scrapfly import TwitterScraperNew

async def debug_scraper():
    """Debug the scraper comprehensively"""
    load_dotenv()
    load_dotenv(dotenv_path='../.env')
    
    print("=== AI Summary Agent Debug Test ===\n")
    
    # Check environment variables
    scrapfly_key = os.getenv("SCRAPFLY_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")
    slack_url = os.getenv("SLACK_WEBHOOK_URL")
    
    print("Environment Check:")
    print(f"   Scrapfly API Key: {'Found' if scrapfly_key else 'Missing'}")
    print(f"   OpenAI API Key: {'Found' if openai_key else 'Missing'}")
    print(f"   Slack Webhook: {'Found' if slack_url else 'Missing'}")
    print()
    
    # Test with one account first
    test_account = "OpenAI"
    
    try:
        async with TwitterScraperNew() as scraper:
            print(f"Testing scraping for @{test_account}...")
            
            # Test the main method (which tries Scrapfly first)
            tweets = await scraper.scrape_user_timeline(test_account, max_tweets=10)
            print(f"Found: {len(tweets)} tweets")
            
            if tweets:
                print(f"\nAnalysis of {len(tweets)} tweets:")
                
                # Show current time for reference
                utc = timezone.utc
                now = datetime.now(utc)
                cutoff_48h = now - timedelta(hours=48)
                
                print(f"   Current time: {now}")
                print(f"   48h cutoff: {cutoff_48h}")
                print()
                
                recent_count = 0
                
                for i, tweet in enumerate(tweets[:5]):
                    text = tweet.get('text', 'No text')[:80]
                    created = tweet.get('created_at', 'No date')
                    likes = tweet.get('favorite_count', 0)
                    tweet_id = tweet.get('id', 'No ID')
                    source = tweet.get('source', 'unknown')
                    
                    print(f"   {i+1}. ID: {tweet_id} (via {source})")
                    print(f"      Date: {created}")
                    print(f"      Text: {text}...")
                    print(f"      Likes: {likes}")
                    
                    # Test date filtering
                    is_recent = scraper.is_tweet_recent(tweet)
                    print(f"      Is Recent (48h): {is_recent}")
                    
                    if is_recent:
                        recent_count += 1
                    print()
                
                print(f"Summary:")
                print(f"   Total tweets: {len(tweets)}")
                print(f"   Recent (48h): {recent_count}")
                
                if recent_count == 0:
                    print("\nWARNING: NO RECENT TWEETS FOUND!")
                    print("   This suggests either:")
                    print("   - Date parsing is failing")
                    print("   - All tweets are older than 48 hours")
                    print("   - Scraping is not getting real tweet data")
                else:
                    print(f"\nSUCCESS: Found {recent_count} recent tweets - scraper should work!")
                
            else:
                print("\nERROR: NO TWEETS FOUND!")
                print("   This indicates the scraping methods are not working.")
                print("   Possible issues:")
                print("   - X.com is blocking all requests")
                print("   - Scrapfly configuration is wrong")
                print("   - Account doesn't exist or is private")
                print("   - Network connectivity issues")
            
    except Exception as e:
        print(f"\nError during testing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_scraper())
