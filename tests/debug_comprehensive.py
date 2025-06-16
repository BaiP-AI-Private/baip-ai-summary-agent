#!/usr/bin/env python3
"""
Comprehensive diagnosis script to debug the scraping issues
"""

import asyncio
import os
import sys
import json
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv

# Add the scripts directory to the path
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'scripts'))

from twitter_scraper_scrapfly import TwitterScraperNew

async def comprehensive_test():
    """Test all aspects of the scraping system"""
    load_dotenv()
    load_dotenv(dotenv_path='../.env')
    
    print("=" * 60)
    print("🔍 COMPREHENSIVE SCRAPING DIAGNOSIS")
    print("=" * 60)
    
    # Check environment
    print("\n1. ENVIRONMENT CHECK:")
    scrapfly_key = os.getenv("SCRAPFLY_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY") 
    slack_url = os.getenv("SLACK_WEBHOOK_URL")
    
    print(f"✓ Scrapfly API Key: {'✓ Present' if scrapfly_key else '✗ Missing'}")
    print(f"✓ OpenAI API Key: {'✓ Present' if openai_key else '✗ Missing'}")
    print(f"✓ Slack Webhook: {'✓ Present' if slack_url else '✗ Missing'}")
    
    # Test date logic
    print("\n2. DATE LOGIC TEST:")
    utc = timezone.utc
    now = datetime.now(utc)
    cutoff_72h = now - timedelta(hours=72)
    cutoff_48h = now - timedelta(hours=48)
    cutoff_24h = now - timedelta(hours=24)
    
    print(f"Current time (UTC): {now}")
    print(f"72h cutoff: {cutoff_72h}")
    print(f"48h cutoff: {cutoff_48h}")
    print(f"24h cutoff: {cutoff_24h}")
    
    # Test a few accounts
    test_accounts = ["OpenAI", "xai", "AnthropicAI"]
    
    try:
        async with TwitterScraperNew() as scraper:
            print(f"\n3. SCRAPING TEST (Testing {len(test_accounts)} accounts):")
            
            for username in test_accounts:
                print(f"\n--- Testing @{username} ---")
                
                # Test raw scraping
                tweets = await scraper.scrape_user_timeline(username, max_tweets=10)
                print(f"Raw tweets found: {len(tweets)}")
                
                if tweets:
                    # Analyze tweet dates
                    print("Sample tweets with dates:")
                    for i, tweet in enumerate(tweets[:5]):
                        created_at = tweet.get("created_at", "No date")
                        text_preview = tweet.get("text", "No text")[:60] + "..."
                        
                        # Test date parsing
                        try:
                            if created_at != "No date":
                                tweet_date = datetime.strptime(created_at, "%a %b %d %H:%M:%S %z %Y")
                                hours_ago = (now - tweet_date).total_seconds() / 3600
                                is_recent = scraper.is_tweet_recent(tweet)
                                print(f"  {i+1}. {hours_ago:.1f}h ago - Recent: {is_recent}")
                                print(f"     Text: {text_preview}")
                            else:
                                print(f"  {i+1}. No date - {text_preview}")
                        except Exception as e:
                            print(f"  {i+1}. Date parsing error: {e}")
                    
                    # Test filtering
                    recent_tweets = [t for t in tweets if scraper.is_tweet_recent(t)]
                    print(f"Recent tweets (72h): {len(recent_tweets)}")
                    
                    if recent_tweets:
                        print("✓ Found recent tweets!")
                        break
                    else:
                        print("✗ No recent tweets found")
                else:
                    print("✗ No tweets scraped at all")
                
                # Small delay between accounts
                await asyncio.sleep(2)
            
            print(f"\n4. FULL SYSTEM TEST:")
            all_tweets = await scraper.scrape_all_accounts()
            print(f"Total recent tweets from all accounts: {len(all_tweets)}")
            
            if all_tweets:
                print("\nSample formatted tweets:")
                for i, tweet_text in enumerate(all_tweets[:3]):
                    print(f"  {i+1}. {tweet_text}")
                
                # Test summary generation
                summary = scraper.generate_summary(all_tweets)
                print(f"\nGenerated summary length: {len(summary)} characters")
                print("Summary preview:", summary[:200] + "..." if len(summary) > 200 else summary)
            else:
                print("✗ No recent tweets found across all accounts")
                
    except Exception as e:
        print(f"ERROR during testing: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("🔧 RECOMMENDATIONS:")
    
    if not scrapfly_key:
        print("1. ⚠️  Get Scrapfly API key from https://scrapfly.io")
    else:
        print("1. ✓ Scrapfly configured")
    
    print("2. 📅 Extended date range to 72 hours for better coverage")
    print("3. 🔄 Dynamic rate limiting implemented")
    print("4. 🛡️  Enhanced error handling and fallbacks")
    print("5. 📊 Added comprehensive logging and debugging")

if __name__ == "__main__":
    asyncio.run(comprehensive_test())
