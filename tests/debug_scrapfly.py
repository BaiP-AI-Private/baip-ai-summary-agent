#!/usr/bin/env python3
"""
Debug script to inspect what data Scrapfly is actually returning
"""

import asyncio
import os
import sys
import json
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv

# Add the scripts directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Try to import scrapfly
try:
    from scrapfly import ScrapeConfig, ScrapflyClient
    SCRAPFLY_AVAILABLE = True
except ImportError:
    SCRAPFLY_AVAILABLE = False

async def debug_scrapfly_data():
    """Debug what data Scrapfly is actually returning"""
    load_dotenv()
    load_dotenv(dotenv_path='../.env')
    
    print("=== Scrapfly Data Debug ===\n")
    
    if not SCRAPFLY_AVAILABLE:
        print("ERROR: Scrapfly not available")
        return
    
    scrapfly_key = os.getenv("SCRAPFLY_API_KEY")
    if not scrapfly_key:
        print("ERROR: No Scrapfly API key")
        return
    
    test_account = "OpenAI"
    url = f"https://x.com/{test_account}"
    
    print(f"Testing: {url}")
    
    try:
        scrapfly = ScrapflyClient(key=scrapfly_key)
        
        result = await scrapfly.async_scrape(ScrapeConfig(
            url,
            render_js=True,
            wait_for_selector="[data-testid='primaryColumn']",
            auto_scroll=True,
            cache=False,
            country="US",
            proxy_pool="public_residential_pool",
            asp=True,
            lang=["en-US"]
        ))
        
        print(f"Status Code: {result.status_code}")
        print(f"Content Length: {len(result.scrape_result.get('result', {}).get('content', ''))}")
        
        # Check browser data
        browser_data = result.scrape_result.get("browser_data", {})
        xhr_calls = browser_data.get("xhr_call", [])
        
        print(f"XHR Calls Found: {len(xhr_calls)}")
        
        if xhr_calls:
            print("\nXHR URLs (first 10):")
            for i, xhr in enumerate(xhr_calls[:10]):
                url_text = xhr.get("url", "No URL")
                method = xhr.get("method", "No method")
                status = xhr.get("response", {}).get("status", "No status")
                print(f"  {i+1}. {method} {status} - {url_text[:100]}...")
            
            # Look for Twitter API calls
            twitter_calls = []
            for xhr in xhr_calls:
                url_text = xhr.get("url", "")
                if any(keyword in url_text for keyword in ["UserTweets", "UserBy", "UserMedia", "graphql", "api", "timeline"]):
                    twitter_calls.append(xhr)
            
            print(f"\nPotential Twitter API calls: {len(twitter_calls)}")
            for i, xhr in enumerate(twitter_calls[:5]):
                url_text = xhr.get("url", "")
                method = xhr.get("method", "GET")
                print(f"  {i+1}. {method} - {url_text}")
                
                # Try to parse response
                try:
                    response_body = xhr.get("response", {}).get("body")
                    if response_body:
                        data = json.loads(response_body)
                        print(f"      Response keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
                except Exception as e:
                    print(f"      Parse error: {e}")
        
        # Check HTML content for tweets
        content = result.scrape_result.get("result", {}).get("content", "")
        tweet_indicators = [
            'data-testid="tweet"',
            'data-testid="cellInnerDiv"',
            '"tweet_results"',
            '"legacy"',
            '"full_text"'
        ]
        
        print(f"\nHTML Content Analysis:")
        for indicator in tweet_indicators:
            count = content.count(indicator)
            print(f"  '{indicator}': {count} occurrences")
        
        # Save a sample of the content for manual inspection
        if content:
            with open("scrapfly_debug_output.html", "w", encoding="utf-8") as f:
                f.write(content[:50000])  # First 50k chars
            print(f"\nSaved first 50k chars to: scrapfly_debug_output.html")
        
        # Check if we can find any structured data in the HTML
        if '"legacy"' in content and '"full_text"' in content:
            print("\n✅ Found structured tweet data in HTML content!")
            print("   This suggests tweets are being loaded but not captured via XHR")
        else:
            print("\n❌ No structured tweet data found in HTML")
            print("   This suggests either no tweets loaded or they're in XHR only")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_scrapfly_data())
