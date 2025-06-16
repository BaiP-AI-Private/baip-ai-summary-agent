#!/usr/bin/env python3
"""
Test script to pull raw OpenAI data for inspection
Saves unfiltered scraped data to text file for analysis
"""

import os
import json
import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional
from dotenv import load_dotenv

# Try to import playwright
try:
    from playwright.async_api import async_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

# Try to import scrapfly
try:
    from scrapfly import ScrapeConfig, ScrapflyClient
    SCRAPFLY_AVAILABLE = True
except ImportError:
    SCRAPFLY_AVAILABLE = False

# Alternative imports for fallback methods
try:
    import requests
    from bs4 import BeautifulSoup
    import jmespath
    FALLBACK_AVAILABLE = True
except ImportError:
    FALLBACK_AVAILABLE = False

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('../openai_test_scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
load_dotenv(dotenv_path='../.env')

class OpenAIDataTester:
    def __init__(self):
        self.scraped_data = []
    async def __aenter__(self):
        if not PLAYWRIGHT_AVAILABLE:
            raise ImportError("Playwright is not available")
        
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-setuid-sandbox']
        )
        self.context = await self.browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
        self.page = await self.context.new_page()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.browser:
            await self.browser.close()
        if hasattr(self, 'playwright'):
            await self.playwright.stop()

    def parse_tweet(self, data: Dict) -> Optional[Dict]:
        """Parse Twitter tweet JSON dataset for detailed analysis"""
        try:
            result = jmespath.search(
                """{
                created_at: legacy.created_at,
                favorite_count: legacy.favorite_count,
                reply_count: legacy.reply_count,
                retweet_count: legacy.retweet_count,
                quote_count: legacy.quote_count,
                text: legacy.full_text,
                user_id: legacy.user_id_str,
                id: legacy.id_str,
                language: legacy.lang,
                views: views.count,
                entities: legacy.entities,
                hashtags: legacy.entities.hashtags[].text,
                urls: legacy.entities.urls[].expanded_url,
                user_mentions: legacy.entities.user_mentions[].screen_name
                }""",
                data,
            )
            
            # Parse user information
            user_data = jmespath.search("core.user_results.result", data)
            if user_data:
                user_info = jmespath.search(
                    """{
                    username: legacy.screen_name,
                    name: legacy.name,
                    verified: legacy.verified,
                    followers_count: legacy.followers_count,
                    following_count: legacy.friends_count
                    }""",
                    user_data
                )
                result["user"] = user_info
            
            return result
        except Exception as e:
            logger.error(f"Error parsing tweet data: {e}")
            return None
    def parse_user_timeline_tweets(self, data: Dict) -> List[Dict]:
        """Parse user timeline response to extract all tweets (no filtering)"""
        tweets = []
        try:
            instructions = jmespath.search("data.user.result.timeline_v2.timeline.instructions", data) or []
            
            for instruction in instructions:
                if instruction.get("type") == "TimelineAddEntries":
                    entries = instruction.get("entries", [])
                    for entry in entries:
                        if entry.get("entryId", "").startswith("tweet-"):
                            tweet_data = jmespath.search("content.itemContent.tweet_results.result", entry)
                            if tweet_data and "legacy" in tweet_data:
                                parsed_tweet = self.parse_tweet(tweet_data)
                                if parsed_tweet:
                                    tweets.append(parsed_tweet)
                                    
        except Exception as e:
            logger.error(f"Error parsing timeline tweets: {e}")
            
        return tweets

    async def scrape_openai_profile(self, max_tweets: int = 50) -> List[Dict]:
        """Scrape OpenAI's X.com profile for recent tweets (unfiltered)"""
        url = "https://x.com/OpenAI"
        logger.info(f"Scraping OpenAI profile: {url}")
        
        xhr_calls = []
        
        def handle_response(response):
            if "xhr" in response.request.resource_type:
                xhr_calls.append(response)
        
        self.page.on("response", handle_response)
        
        try:
            # Navigate to OpenAI profile
            await self.page.goto(url, wait_until="networkidle", timeout=30000)
            
            # Wait for tweets to load
            try:
                await self.page.wait_for_selector("[data-testid='tweet']", timeout=15000)
            except:
                logger.warning("No tweets found or page load timeout")
                return []
            
            # Scroll to load more tweets
            for i in range(3):  # Scroll 3 times to get more content
                await self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await asyncio.sleep(2)
            
            # Look for UserTweets background requests
            timeline_calls = []
            for xhr in xhr_calls:
                if xhr.url and ("UserTweets" in xhr.url or "UserMedia" in xhr.url):
                    try:
                        response_data = await xhr.json()
                        timeline_calls.append(response_data)
                    except Exception as e:
                        logger.debug(f"Could not parse XHR response: {e}")
                        continue
            
            tweets = []
            for timeline_data in timeline_calls:
                parsed_tweets = self.parse_user_timeline_tweets(timeline_data)
                tweets.extend(parsed_tweets)
                if len(tweets) >= max_tweets:
                    break
            
            # Remove duplicates based on tweet ID
            seen_ids = set()
            unique_tweets = []
            for tweet in tweets:
                tweet_id = tweet.get("id")
                if tweet_id and tweet_id not in seen_ids:
                    seen_ids.add(tweet_id)
                    unique_tweets.append(tweet)
            
            logger.info(f"Found {len(unique_tweets)} unique tweets from OpenAI")
            return unique_tweets[:max_tweets]
            
        except Exception as e:
            logger.error(f"Error scraping OpenAI profile: {e}")
            return []

    async def scrape_openai_scrapfly(self, max_tweets: int = 50) -> List[Dict]:
        """Scrape OpenAI's X.com profile using Scrapfly method"""
        if not SCRAPFLY_AVAILABLE:
            logger.error("Scrapfly not available")
            return []
        
        # Check for Scrapfly API key
        scrapfly_key = os.getenv("SCRAPFLY_API_KEY")
        if not scrapfly_key:
            logger.warning("SCRAPFLY_API_KEY not found in environment, using demo mode")
            # For demo purposes, we can still show the structure
            return []
        
        url = "https://x.com/OpenAI"
        logger.info(f"Scraping OpenAI profile with Scrapfly: {url}")
        
        try:
            scrapfly = ScrapflyClient(key=scrapfly_key)
            
            result = await scrapfly.async_scrape(ScrapeConfig(
                url,
                render_js=True,  # Enable headless browser
                wait_for_selector="[data-testid='tweet']",  # Wait for tweets to load
                cache=False,  # Don't use cache for fresh data
                country="US",  # Use US proxy
                proxy_pool="public_residential_pool"  # Use residential proxies
            ))
            
            # Extract XHR calls from browser data
            xhr_calls = result.scrape_result.get("browser_data", {}).get("xhr_call", [])
            
            tweets = []
            for xhr in xhr_calls:
                if xhr.get("url") and ("UserTweets" in xhr["url"] or "UserMedia" in xhr["url"]):
                    try:
                        if xhr.get("response", {}).get("body"):
                            response_data = json.loads(xhr["response"]["body"])
                            parsed_tweets = self.parse_user_timeline_tweets(response_data)
                            tweets.extend(parsed_tweets)
                            if len(tweets) >= max_tweets:
                                break
                    except Exception as e:
                        logger.debug(f"Could not parse Scrapfly XHR response: {e}")
                        continue
            
            # Remove duplicates based on tweet ID
            seen_ids = set()
            unique_tweets = []
            for tweet in tweets:
                tweet_id = tweet.get("id")
                if tweet_id and tweet_id not in seen_ids:
                    seen_ids.add(tweet_id)
                    tweet["source"] = "scrapfly"  # Mark source
                    unique_tweets.append(tweet)
            
            logger.info(f"Found {len(unique_tweets)} unique tweets via Scrapfly")
            return unique_tweets[:max_tweets]
            
        except Exception as e:
            logger.error(f"Error scraping with Scrapfly: {e}")
            return []
    def fallback_scrape_openai(self) -> List[Dict]:
        """Fallback method using Nitter instances"""
        if not FALLBACK_AVAILABLE:
            logger.error("Fallback dependencies not available")
            return []
        
        nitter_instances = [
            "https://nitter.net",
            "https://nitter.unixfox.eu",
            "https://nitter.kavin.rocks"
        ]
        
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        for instance in nitter_instances:
            try:
                url = f"{instance}/OpenAI"
                logger.info(f"Trying Nitter instance: {url}")
                
                response = session.get(url, timeout=15)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    tweets = []
                    
                    # Parse Nitter HTML structure
                    tweet_containers = soup.select('div.timeline-item')
                    for container in tweet_containers:
                        try:
                            text_element = container.find('div', class_='tweet-content')
                            date_element = container.find('span', class_='tweet-date')
                            
                            if text_element and date_element:
                                tweet_data = {
                                    'text': text_element.get_text(strip=True),
                                    'created_at': date_element.get('title', ''),
                                    'source': 'nitter',
                                    'user': {'username': 'OpenAI'}
                                }
                                tweets.append(tweet_data)
                        except Exception as e:
                            logger.debug(f"Error parsing Nitter tweet: {e}")
                            continue
                    
                    if tweets:
                        logger.info(f"Found {len(tweets)} tweets via Nitter")
                        return tweets
                        
            except Exception as e:
                logger.debug(f"Nitter instance {instance} failed: {e}")
                continue
        
        logger.warning("All Nitter instances failed")
        return []

    def format_tweet_for_output(self, tweet: Dict, index: int) -> str:
        """Format tweet data for text file output"""
        output = f"\n{'='*80}\n"
        output += f"TWEET #{index + 1}\n"
        output += f"{'='*80}\n"
        
        # Basic tweet info
        output += f"ID: {tweet.get('id', 'Unknown')}\n"
        output += f"Date: {tweet.get('created_at', 'Unknown')}\n"
        output += f"Language: {tweet.get('language', 'Unknown')}\n"
        output += f"Source: {tweet.get('source', 'X.com')}\n\n"
        
        # Tweet content
        output += f"TEXT:\n{tweet.get('text', 'No text available')}\n\n"
        
        # Engagement metrics
        output += f"ENGAGEMENT:\n"
        output += f"  Likes: {tweet.get('favorite_count', 0):,}\n"
        output += f"  Retweets: {tweet.get('retweet_count', 0):,}\n"
        output += f"  Replies: {tweet.get('reply_count', 0):,}\n"
        output += f"  Quotes: {tweet.get('quote_count', 0):,}\n"
        output += f"  Views: {tweet.get('views', 'N/A')}\n\n"
        
        # User info
        user = tweet.get('user', {})
        if user:
            output += f"USER INFO:\n"
            output += f"  Username: @{user.get('username', 'OpenAI')}\n"
            output += f"  Display Name: {user.get('name', 'OpenAI')}\n"
            output += f"  Verified: {user.get('verified', False)}\n"
            output += f"  Followers: {user.get('followers_count', 'N/A')}\n\n"
        
        # Additional data
        hashtags = tweet.get('hashtags', [])
        if hashtags:
            output += f"HASHTAGS: {', '.join(hashtags)}\n\n"
        
        urls = tweet.get('urls', [])
        if urls:
            output += f"URLS:\n"
            for url in urls:
                output += f"  - {url}\n"
            output += "\n"
        
        mentions = tweet.get('user_mentions', [])
        if mentions:
            output += f"MENTIONS: {', '.join(f'@{m}' for m in mentions)}\n\n"
        
        return output
    def save_data_to_file(self, playwright_tweets: List[Dict] = None, scrapfly_tweets: List[Dict] = None, nitter_tweets: List[Dict] = None, filename: str = None):
        """Save scraped data from multiple sources to text file for inspection"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"../openai_scraped_data_{timestamp}.txt"
        
        # Combine all tweets with source marking
        all_tweets = []
        if playwright_tweets:
            for tweet in playwright_tweets:
                tweet["source"] = "playwright"
                all_tweets.append(tweet)
        if scrapfly_tweets:
            for tweet in scrapfly_tweets:
                tweet["source"] = "scrapfly"
                all_tweets.append(tweet)
        if nitter_tweets:
            for tweet in nitter_tweets:
                tweet["source"] = "nitter"
                all_tweets.append(tweet)
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                # Header
                f.write("OpenAI X.com Profile - Raw Scraped Data (Multi-Source Comparison)\n")
                f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Total Tweets: {len(all_tweets)}\n")
                
                # Source breakdown
                sources = {}
                for tweet in all_tweets:
                    source = tweet.get("source", "unknown")
                    sources[source] = sources.get(source, 0) + 1
                
                f.write(f"Data Sources Used:\n")
                for source, count in sources.items():
                    f.write(f"  - {source.title()}: {count} tweets\n")
                
                f.write("="*80 + "\n")
                
                # Separate sections for each source
                for source in ["playwright", "scrapfly", "nitter"]:
                    source_tweets = [t for t in all_tweets if t.get("source") == source]
                    if source_tweets:
                        f.write(f"\n{source.upper()} METHOD RESULTS\n")
                        f.write("="*80 + "\n")
                        f.write(f"Found {len(source_tweets)} tweets using {source} method\n")
                        
                        # Quick summary for this source
                        if source_tweets:
                            total_likes = sum(tweet.get('favorite_count', 0) for tweet in source_tweets)
                            total_retweets = sum(tweet.get('retweet_count', 0) for tweet in source_tweets)
                            f.write(f"Total Likes: {total_likes:,}\n")
                            f.write(f"Total Retweets: {total_retweets:,}\n")
                            if len(source_tweets) > 0:
                                f.write(f"Average Likes per Tweet: {total_likes//len(source_tweets):,}\n")
                                f.write(f"Average Retweets per Tweet: {total_retweets//len(source_tweets):,}\n")
                        
                        f.write("\n" + "-"*80 + "\n")
                        f.write(f"DETAILED TWEETS - {source.upper()} METHOD\n")
                        f.write("-"*80 + "\n")
                        
                        for i, tweet in enumerate(source_tweets):
                            f.write(self.format_tweet_for_output(tweet, i))
                    else:
                        f.write(f"\n{source.upper()} METHOD RESULTS\n")
                        f.write("="*80 + "\n")
                        f.write(f"No tweets found using {source} method\n")
                        if source == "scrapfly" and not SCRAPFLY_AVAILABLE:
                            f.write("(Scrapfly SDK not available)\n")
                        elif source == "playwright" and not PLAYWRIGHT_AVAILABLE:
                            f.write("(Playwright not available)\n")
                        elif source == "nitter" and not FALLBACK_AVAILABLE:
                            f.write("(Fallback dependencies not available)\n")
                
                # Combined analysis if multiple sources have data
                if len([s for s in sources.keys() if sources[s] > 0]) > 1:
                    f.write(f"\nCOMBINED ANALYSIS\n")
                    f.write("="*80 + "\n")
                    f.write("Comparison of methods:\n")
                    for source, count in sources.items():
                        if count > 0:
                            source_tweets = [t for t in all_tweets if t.get("source") == source]
                            avg_engagement = sum(t.get('favorite_count', 0) + t.get('retweet_count', 0) 
                                               for t in source_tweets) / len(source_tweets) if source_tweets else 0
                            f.write(f"  {source.title()}: {count} tweets, avg engagement: {avg_engagement:.0f}\n")
                
                # Footer
                f.write("\n" + "="*80 + "\n")
                f.write("END OF DATA\n")
                f.write("="*80 + "\n")
            
            logger.info(f"Data saved to: {filename}")
            print(f"✓ Data saved to: {filename}")
            return filename
            
        except Exception as e:
            logger.error(f"Error saving data to file: {e}")
            return None

async def main():
    """Main execution function"""
    print("OpenAI Data Test Scraper - Multi-Method Comparison")
    print("=" * 60)
    print("This script tests multiple scraping methods and compares results.\n")
    
    playwright_tweets = []
    scrapfly_tweets = []
    nitter_tweets = []
    
    try:
        # Test Playwright method
        if PLAYWRIGHT_AVAILABLE:
            print("🎭 Testing Playwright method...")
            try:
                async with OpenAIDataTester() as scraper:
                    playwright_tweets = await scraper.scrape_openai_profile(max_tweets=50)
                    if playwright_tweets:
                        print(f"  ✓ Playwright: Found {len(playwright_tweets)} tweets")
                    else:
                        print(f"  ⚠ Playwright: No tweets found")
            except Exception as e:
                print(f"  ✗ Playwright failed: {e}")
        else:
            print("🎭 Playwright not available (install: pip install playwright)")
        
        # Test Scrapfly method  
        if SCRAPFLY_AVAILABLE:
            print("🚀 Testing Scrapfly method...")
            try:
                scraper = OpenAIDataTester()
                scrapfly_tweets = await scraper.scrape_openai_scrapfly(max_tweets=50)
                if scrapfly_tweets:
                    print(f"  ✓ Scrapfly: Found {len(scrapfly_tweets)} tweets")
                else:
                    print(f"  ⚠ Scrapfly: No tweets found")
            except Exception as e:
                print(f"  ✗ Scrapfly failed: {e}")
        else:
            print("🚀 Scrapfly not available (install: pip install scrapfly-sdk)")
        
        # Test Nitter fallback method
        if FALLBACK_AVAILABLE:
            print("🔄 Testing Nitter fallback method...")
            try:
                scraper = OpenAIDataTester()
                nitter_tweets = scraper.fallback_scrape_openai()
                if nitter_tweets:
                    print(f"  ✓ Nitter: Found {len(nitter_tweets)} tweets")
                else:
                    print(f"  ⚠ Nitter: No tweets found")
            except Exception as e:
                print(f"  ✗ Nitter failed: {e}")
        else:
            print("🔄 Nitter fallback not available (missing dependencies)")
        
        # Summary of results
        total_tweets = len(playwright_tweets) + len(scrapfly_tweets) + len(nitter_tweets)
        print(f"\n📊 Results Summary:")
        print(f"  Playwright: {len(playwright_tweets)} tweets")
        print(f"  Scrapfly:   {len(scrapfly_tweets)} tweets")
        print(f"  Nitter:     {len(nitter_tweets)} tweets")
        print(f"  Total:      {total_tweets} tweets")
        
        # Save data with method comparison
        if total_tweets > 0:
            scraper = OpenAIDataTester()
            filename = scraper.save_data_to_file(
                playwright_tweets=playwright_tweets,
                scrapfly_tweets=scrapfly_tweets, 
                nitter_tweets=nitter_tweets
            )
            
            if filename:
                print(f"\n✓ Success! Multi-method comparison saved to: {filename}")
                print("\nThe file contains separate sections for each method so you can")
                print("compare which approach works best and see the data differences.")
            else:
                print("✗ Failed to save comparison data")
        else:
            print("\n⚠ No tweets found from any method")
            # Save empty file with method status for debugging
            scraper = OpenAIDataTester()
            scraper.save_data_to_file()
            
    except Exception as e:
        logger.error(f"Critical error: {e}")
        print(f"✗ Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())