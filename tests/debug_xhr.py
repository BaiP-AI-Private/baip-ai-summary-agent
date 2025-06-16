#!/usr/bin/env python3
"""
Debug XHR URLs from Scrapfly
"""

import asyncio
import os
import sys
import json
import logging
from dotenv import load_dotenv

# Add the scripts directory to the path
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'scripts'))

# Set debug logging
logging.basicConfig(level=logging.DEBUG)

from twitter_scraper_scrapfly import TwitterScraperNew

async def debug_xhr_urls():
    """Test to see what XHR URLs we're getting from Scrapfly"""
    load_dotenv()
    load_dotenv(dotenv_path='../.env')
    
    print("=" * 50)
    print("XHR DEBUG TEST")
    print("=" * 50)
    
    scrapfly_key = os.getenv("SCRAPFLY_API_KEY")
    if not scrapfly_key:
        print("No Scrapfly API key found")
        return
    
    try:
        async with TwitterScraperNew() as scraper:
            print("Testing Scrapfly XHR capture for OpenAI...")
            
            # This will show debug output of XHR URLs
            tweets = await scraper.scrape_user_timeline("OpenAI", max_tweets=5)
            print(f"\nResult: {len(tweets)} tweets found")
            
            if tweets:
                for i, tweet in enumerate(tweets[:2]):
                    print(f"Tweet {i+1}: {tweet.get('text', 'No text')[:100]}...")
            else:
                print("No tweets found - check XHR URLs above")
                
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_xhr_urls())
