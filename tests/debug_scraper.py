#!/usr/bin/env python3
"""
Comprehensive debug test for the Twitter scraper
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
    
    print("🔑 Environment Check:")
    print(f"   Scrapfly API Key: {'✅ Found' if scrapfly_key else '❌ Missing'}")
    print(f"   OpenAI API Key: {'✅ Found' if openai_key else '❌ Missing'}")
    print(f"   Slack Webhook: {'✅ Found' if slack_url else '❌ Missing'}")
    print()
    
    # Test with one account first
    test_account = "OpenAI"
    
    try:
        async with TwitterScraperNew() as scraper:
            print(f"🔍 Testing scraping for @{test_account}...")
            
            # Test both methods
            print("\n--- Testing Scrapfly Method ---")
            scrapfly_tweets = await scraper.scrape_user_timeline_scrapfly(test_account, max_tweets=10)
            print(f"Scrapfly found: {len(scrapfly_tweets)} tweets")
            
            print("\n--- Testing Playwright Method ---")
            playwright_tweets = await scraper.scrape_user_timeline_playwright(test_account, max_tweets=10)
            print(f"Playwright found: {len(playwright_tweets)} tweets")
            
            # Use whichever method found tweets
            tweets = scrapfly_tweets if scrapfly_tweets else playwright_tweets
            method_used = "Scrapfly" if scrapfly_tweets else "Playwright"
            
            if tweets:
                print(f"\n📊 Analysis of {len(tweets)} tweets from {method_used}:")
                
                # Show current time for reference
                utc = timezone.utc
                now = datetime.now(utc)
                cutoff_24h = now - timedelta(hours=24)
                cutoff_48h = now - timedelta(hours=48)
                
                print(f"   Current time: {now}")
                print(f"   24h cutoff: {cutoff_24h}")
                print(f"   48h cutoff: {cutoff_48h}")
                print()
                
                recent_24h = 0
                recent_48h = 0
                
                for i, tweet in enumerate(tweets[:5]):
                    text = tweet.get('text', 'No text')[:80]
                    created = tweet.get('created_at', 'No date')
                    likes = tweet.get('favorite_count', 0)
                    tweet_id = tweet.get('id', 'No ID')
                    
                    print(f"   {i+1}. ID: {tweet_id}")
                    print(f"      Date: {created}")
                    print(f"      Text: {text}...")
                    print(f"      Likes: {likes}")
                    
                    # Test date filtering
                    is_recent = scraper.is_tweet_recent(tweet)
                    print(f"      Recent (48h): {is_recent}")
                    
                    if is_recent:
                        recent_48h += 1
                        # Check if also within 24h
                        try:
                            if created:
                                tweet_date = datetime.strptime(created, "%a %b %d %H:%M:%S %z %Y")
                                if tweet_date >= cutoff_24h:
                                    recent_24h += 1
                        except:
                            pass
                    print()
                
                print(f"📈 Summary:")
                print(f"   Total tweets: {len(tweets)}")
                print(f"   Recent (24h): {recent_24h}")
                print(f"   Recent (48h): {recent_48h}")
                
                if recent_48h == 0:
                    print("\n⚠️  NO RECENT TWEETS FOUND!")
                    print("   This suggests either:")
                    print("   - Date parsing is failing")
                    print("   - All tweets are older than 48 hours")
                    print("   - Scraping is not getting real tweet data")
                else:
                    print(f"\n✅ Found {recent_48h} recent tweets - scraper should work!")
                
            else:
                print("\n❌ NO TWEETS FOUND!")
                print("   This indicates the scraping methods are not working.")
                print("   Possible issues:")
                print("   - X.com is blocking all requests")
                print("   - Scrapfly configuration is wrong")
                print("   - Account doesn't exist or is private")
                print("   - Network connectivity issues")
            
    except Exception as e:
        print(f"\n💥 Error during testing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_scraper())
