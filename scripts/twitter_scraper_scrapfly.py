"""
Modern Twitter/X.com scraper using Playwright and background request capture
Based on Scrapfly method for reliable tweet extraction
"""

import os
import json
import asyncio
import logging
import jmespath
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional
from openai import OpenAI
import requests
from dotenv import load_dotenv

# Try to import scrapfly
try:
    from scrapfly import ScrapeConfig, ScrapflyClient
    SCRAPFLY_AVAILABLE = True
except ImportError:
    SCRAPFLY_AVAILABLE = False

# Try to import playwright as fallback
try:
    from playwright.async_api import async_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('tweet_scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
load_dotenv(dotenv_path='../.env')

# Initialize OpenAI client
api_key = os.getenv("OPENAI_API_KEY")
client = None
if api_key:
    try:
        client = OpenAI(api_key=api_key)
    except Exception as e:
        logger.error(f"Failed to initialize OpenAI client: {e}")

# Configuration
X_ACCOUNTS = ["OpenAI", "xai", "AnthropicAI", "GoogleDeepMind", "MistralAI",
              "AIatMeta", "Cohere", "perplexity_ai", "scale_ai", "runwayml", "dair_ai"]

class TwitterScraperNew:
    def __init__(self):
        self.browser = None
        self.context = None
        self.page = None

    async def __aenter__(self):
        if not PLAYWRIGHT_AVAILABLE:
            raise ImportError("Playwright is not available")
        
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=True,
            args=[
                '--no-sandbox', 
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-accelerated-2d-canvas',
                '--no-first-run',
                '--no-zygote',
                '--disable-gpu',
                '--disable-background-timer-throttling',
                '--disable-backgrounding-occluded-windows',
                '--disable-renderer-backgrounding'
            ]
        )
        self.context = await self.browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        self.page = await self.context.new_page()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.browser:
            await self.browser.close()
        if hasattr(self, 'playwright'):
            await self.playwright.stop()

    def parse_tweet(self, data: Dict) -> Optional[Dict]:
        """Parse Twitter tweet JSON dataset for the most important fields"""
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
                views: views.count
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
                    verified: legacy.verified
                    }""",
                    user_data
                )
                result["user"] = user_info
            
            return result
        except Exception as e:
            logger.error(f"Error parsing tweet data: {e}")
            return None
    def parse_user_timeline_tweets(self, data: Dict) -> List[Dict]:
        """Parse user timeline response to extract tweets"""
        tweets = []
        try:
            # Navigate through the timeline response structure
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

    def parse_alternative_timeline(self, data: Dict) -> List[Dict]:
        """Alternative parsing method for different X.com API structures"""
        tweets = []
        try:
            # Try different JSON structures
            possible_paths = [
                "data.user.result.timeline.timeline.instructions",
                "data.home.home_timeline_urt.instructions", 
                "data.timeline.timeline.instructions",
                "timeline.instructions",
                "instructions"
            ]
            
            instructions = None
            for path in possible_paths:
                instructions = jmespath.search(path, data)
                if instructions:
                    logger.debug(f"Found instructions at path: {path}")
                    break
            
            if not instructions:
                return tweets
            
            for instruction in instructions:
                if instruction.get("type") in ["TimelineAddEntries", "TimelineReplaceEntry"]:
                    entries = instruction.get("entries", [])
                    for entry in entries:
                        entry_id = entry.get("entryId", "")
                        if any(pattern in entry_id for pattern in ["tweet-", "homeConversation-", "profile-conversation-"]):
                            # Try multiple tweet data paths
                            tweet_paths = [
                                "content.itemContent.tweet_results.result",
                                "content.itemContent.result", 
                                "content.item.content.result",
                                "item.content.result"
                            ]
                            
                            for path in tweet_paths:
                                tweet_data = jmespath.search(path, entry)
                                if tweet_data and "legacy" in tweet_data:
                                    parsed_tweet = self.parse_tweet(tweet_data)
                                    if parsed_tweet:
                                        tweets.append(parsed_tweet)
                                        break
                                        
        except Exception as e:
            logger.debug(f"Error in alternative parsing: {e}")
            
        return tweets

    async def scrape_user_timeline_scrapfly(self, username: str, max_tweets: int = 10) -> List[Dict]:
        """Scrape user timeline using Scrapfly (more reliable)"""
        if not SCRAPFLY_AVAILABLE:
            logger.warning("Scrapfly not available, falling back to Playwright")
            return await self.scrape_user_timeline_playwright(username, max_tweets)
        
        # Check for Scrapfly API key
        scrapfly_key = os.getenv("SCRAPFLY_API_KEY")
        if not scrapfly_key:
            logger.warning("SCRAPFLY_API_KEY not found, falling back to Playwright")
            return await self.scrape_user_timeline_playwright(username, max_tweets)
        
        url = f"https://x.com/{username}"
        logger.info(f"Scraping timeline for @{username} using Scrapfly")
        
        try:
            scrapfly = ScrapflyClient(key=scrapfly_key)
            
            result = await scrapfly.async_scrape(ScrapeConfig(
                url,
                render_js=True,  # Enable headless browser
                wait_for_selector="[data-testid='tweet']",  # Wait for tweets specifically
                cache=False,  # Don't use cache for fresh data
                country="US",  # Use US proxy
                proxy_pool="public_residential_pool",  # Use residential proxies
                asp=True,  # Enable ASP for better success rate
                rendering_wait=2000,  # Reduced wait time
                js_scenario=[  # Simplified scrolling
                    {"wait": 1000},
                    {"scroll": {"y": 1000}},
                    {"wait": 1000},
                    {"scroll": {"y": 2000}},
                    {"wait": 1000}
                ]
            ))
            
            logger.info(f"Scrapfly response status: {result.response.status_code}")
            
            # Check if we got blocked or redirected
            if result.response.status_code != 200:
                logger.warning(f"Scrapfly returned status {result.response.status_code}, falling back to Playwright")
                return await self.scrape_user_timeline_playwright(username, max_tweets)
            
            # Extract XHR calls from browser data
            browser_data = result.scrape_result.get("browser_data", {})
            xhr_calls = browser_data.get("xhr_call", [])
            
            logger.info(f"Found {len(xhr_calls)} XHR calls from Scrapfly")
            
            # Debug: Log all XHR URLs to see what we're getting
            if logger.getEffectiveLevel() <= 10:  # DEBUG level
                for i, xhr in enumerate(xhr_calls[:10]):  # Log first 10
                    url = xhr.get("url", "No URL")
                    logger.debug(f"XHR {i+1}: {url}")
            
            tweets = []
            for xhr in xhr_calls:
                url_check = xhr.get("url", "")
                # Expanded patterns for different X.com API endpoints
                api_patterns = [
                    "UserTweets", "UserBy", "UserMedia", 
                    "Timeline", "HomeTimeline", "HomeLatest",
                    "usertweets", "profile", "status",
                    "graphql", "adaptive.json", "timeline.json"
                ]
                
                if url_check and any(pattern in url_check for pattern in api_patterns):
                    logger.debug(f"Found matching XHR URL: {url_check[:100]}...")
                    try:
                        response_body = xhr.get("response", {}).get("body")
                        if response_body:
                            response_data = json.loads(response_body)
                            parsed_tweets = self.parse_user_timeline_tweets(response_data)
                            if parsed_tweets:
                                tweets.extend(parsed_tweets)
                                logger.debug(f"Parsed {len(parsed_tweets)} tweets from XHR call")
                            else:
                                # Try alternative parsing methods
                                alt_tweets = self.parse_alternative_timeline(response_data)
                                if alt_tweets:
                                    tweets.extend(alt_tweets)
                                    logger.debug(f"Parsed {len(alt_tweets)} tweets using alternative method")
                            
                            if len(tweets) >= max_tweets * 2:  # Get extra to filter
                                break
                    except Exception as e:
                        logger.debug(f"Could not parse Scrapfly XHR response: {e}")
                        continue
            
            # If no XHR data, try parsing the HTML directly
            if not tweets:
                logger.warning(f"No XHR data found for @{username}, trying HTML parsing")
                # Fallback to basic HTML parsing would go here
                # For now, fall back to Playwright
                return await self.scrape_user_timeline_playwright(username, max_tweets)
            
            # Remove duplicates based on tweet ID
            seen_ids = set()
            unique_tweets = []
            for tweet in tweets:
                tweet_id = tweet.get("id")
                if tweet_id and tweet_id not in seen_ids:
                    seen_ids.add(tweet_id)
                    tweet["source"] = "scrapfly"  # Mark source
                    unique_tweets.append(tweet)
            
            # Filter to most recent tweets
            tweets = unique_tweets[:max_tweets]
            logger.info(f"Found {len(tweets)} tweets for @{username} via Scrapfly")
            return tweets
            
        except Exception as e:
            logger.error(f"Error scraping @{username} with Scrapfly: {e}")
            logger.info(f"Falling back to Playwright for @{username}")
            return await self.scrape_user_timeline_playwright(username, max_tweets)

    async def scrape_user_timeline_playwright(self, username: str, max_tweets: int = 10) -> List[Dict]:
        """Scrape recent tweets from a user's timeline using Playwright (fallback method)"""
        url = f"https://x.com/{username}"
        logger.info(f"Scraping timeline for @{username}")
        
        xhr_calls = []
        
        def handle_response(response):
            if "xhr" in response.request.resource_type:
                xhr_calls.append(response)
        
        self.page.on("response", handle_response)
        
        try:
            # Navigate to the user profile
            await self.page.goto(url, wait_until="networkidle", timeout=30000)
            
            # Wait for the page to load tweets
            try:
                await self.page.wait_for_selector("[data-testid='tweet']", timeout=15000)
            except:
                logger.warning(f"No tweets found for @{username} or page load timeout")
                return []
            
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
            # Filter to most recent tweets
            tweets = tweets[:max_tweets]
            logger.info(f"Found {len(tweets)} tweets for @{username}")
            return tweets
            
        except Exception as e:
            logger.error(f"Error scraping @{username}: {e}")
            return []

    async def scrape_user_timeline(self, username: str, max_tweets: int = 10) -> List[Dict]:
        """Main method to scrape user timeline - tries Scrapfly first, falls back to Playwright"""
        return await self.scrape_user_timeline_scrapfly(username, max_tweets)

    def is_tweet_recent(self, tweet: Dict) -> bool:
        """Check if tweet is from the last 120 hours (5 days for weekend coverage)"""
        try:
            created_at = tweet.get("created_at")
            if not created_at:
                logger.debug("Tweet has no created_at field")
                return False
            
            # Parse Twitter's date format: "Wed Oct 10 20:19:24 +0000 2018"
            tweet_date = datetime.strptime(created_at, "%a %b %d %H:%M:%S %z %Y")
            
            # Get current time and cutoff (last 120 hours for better weekend coverage)
            utc = timezone.utc
            now = datetime.now(utc)
            cutoff_time = now - timedelta(hours=120)  # 5 days to account for weekends
            
            is_recent = tweet_date >= cutoff_time
            
            # Enhanced logging for debugging
            hours_ago = (now - tweet_date).total_seconds() / 3600
            logger.debug(f"Tweet from @{tweet.get('user', {}).get('username', 'unknown')}: {hours_ago:.1f}h ago, Recent: {is_recent}")
            
            return is_recent
            
        except Exception as e:
            logger.error(f"Error parsing tweet date '{created_at}': {e}")
            return False

    def format_tweet_for_summary(self, tweet: Dict, username: str) -> str:
        """Format tweet data for summary generation"""
        text = tweet.get("text", "").strip()
        # Clean up the text - remove extra whitespace and newlines
        text = " ".join(text.split())
        
        # Add engagement metrics if significant
        likes = tweet.get("favorite_count", 0)
        retweets = tweet.get("retweet_count", 0)
        
        engagement_info = ""
        if likes > 1000 or retweets > 100:
            engagement_info = f" [👍{likes} 🔄{retweets}]"
        
        return f"@{username}: {text}{engagement_info}"
    async def scrape_all_accounts(self) -> List[str]:
        """Scrape tweets from all configured accounts with dynamic rate limiting"""
        all_tweets = []
        successful_accounts = 0
        
        # Dynamic rate limiting variables
        base_delay = 1.0  # Start with 1 second
        max_delay = 10.0  # Maximum delay
        success_streak = 0
        
        for i, username in enumerate(X_ACCOUNTS):
            try:
                logger.info(f"Processing @{username} ({i+1}/{len(X_ACCOUNTS)})...")
                
                # Scrape tweets
                tweets = await self.scrape_user_timeline(username, max_tweets=20)
                logger.info(f"Raw tweets found for @{username}: {len(tweets)}")
                
                # Debug: Log some sample tweet dates
                if tweets:
                    for j, tweet in enumerate(tweets[:3]):
                        created_at = tweet.get("created_at", "No date")
                        text_preview = tweet.get("text", "No text")[:50]
                        logger.debug(f"Sample tweet {j+1}: {created_at} - {text_preview}...")
                
                # Filter to recent tweets (last 48 hours)
                recent_tweets = [t for t in tweets if self.is_tweet_recent(t)]
                
                if recent_tweets:
                    for tweet in recent_tweets[:5]:  # Limit to 5 tweets per account
                        formatted_tweet = self.format_tweet_for_summary(tweet, username)
                        all_tweets.append(formatted_tweet)
                    
                    logger.info(f"Found {len(recent_tweets)} recent tweets from @{username}")
                    successful_accounts += 1
                    success_streak += 1
                    
                    # Decrease delay on success
                    base_delay = max(0.5, base_delay * 0.8)
                else:
                    logger.warning(f"No recent tweets found for @{username} (found {len(tweets)} total tweets)")
                    success_streak = 0
                    
                    # Increase delay on no results (might be getting blocked)
                    base_delay = min(max_delay, base_delay * 1.5)
                
                # Dynamic rate limiting based on success
                if i < len(X_ACCOUNTS) - 1:  # Don't delay after last account
                    if success_streak >= 3:
                        # Good streak - use minimal delay
                        delay = max(0.5, base_delay)
                    elif successful_accounts == 0 and i >= 2:
                        # No success yet - increase delay significantly
                        delay = min(max_delay, base_delay * 2)
                    else:
                        delay = base_delay
                    
                    logger.debug(f"Rate limiting: waiting {delay:.1f}s (base: {base_delay:.1f}s, streak: {success_streak})")
                    await asyncio.sleep(delay)
                
            except Exception as e:
                logger.error(f"Failed to process @{username}: {e}")
                success_streak = 0
                base_delay = min(max_delay, base_delay * 1.2)
                continue
        
        logger.info(f"Successfully processed {successful_accounts}/{len(X_ACCOUNTS)} accounts")
        logger.info(f"Total tweets collected: {len(all_tweets)}")
        
        # Log current time for debugging
        utc = timezone.utc
        current_time = datetime.now(utc)
        logger.info(f"Scraping completed at: {current_time} UTC")
        logger.info(f"Looking for tweets from last 120 hours (since {current_time - timedelta(hours=120)})")
        
        # Enhanced debugging
        if successful_accounts == 0:
            logger.error("🚨 CRITICAL: No accounts were successfully scraped!")
            logger.error("This suggests either:")
            logger.error("1. Scrapfly API issues or rate limits")
            logger.error("2. X.com has updated their structure")
            logger.error("3. All accounts genuinely have no recent posts (very unlikely)")
        elif len(all_tweets) == 0:
            logger.warning("⚠️  Scraping succeeded but no recent tweets found")
            logger.warning("This might indicate:")
            logger.warning("1. Date filtering is too restrictive")
            logger.warning("2. Tweet parsing is failing")
            logger.warning("3. Genuinely quiet period (unlikely for all AI companies)")
        
        return all_tweets

    def generate_summary(self, tweets: List[str]) -> str:
        """Generate AI summary of tweets"""
        if not tweets:
            return "No tweets found from monitored AI companies in the last 5 days."
        
        # Combine tweets for analysis
        tweets_text = "\n\n".join(tweets[:25])  # Limit to prevent token overflow
        
        # Get current time for context
        utc = timezone.utc
        current_time = datetime.now(utc)
        
        prompt = f"""Analyze these tweets from AI companies posted in the last 5 days and create a concise business week summary:

Current time: {current_time.strftime('%Y-%m-%d %H:%M UTC')}

Key points to extract:
- New product announcements
- Technical breakthroughs
- Important partnerships
- Notable research findings
- Significant company updates
- Industry trends and insights
- Major business developments

Please format the summary as a professional business intelligence briefing with clear bullet points, prioritizing the most important information first. Focus on developments that would impact the AI industry or business strategy.

Tweets from the last 5 business days:
{tweets_text}

Summary:"""
        try:
            if client:
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.3,
                    max_tokens=600
                )
                return response.choices[0].message.content.strip()
            else:
                logger.warning("OpenAI client not available, generating manual summary")
                return self.generate_manual_summary(tweets)
                
        except Exception as e:
            logger.error(f"Error generating AI summary: {e}")
            return self.generate_manual_summary(tweets)

    def generate_manual_summary(self, tweets: List[str]) -> str:
        """Generate a professional summary when AI is unavailable"""
        current_time = datetime.now(timezone.utc)
        summary = f"**AI Business Week Summary - Manual Analysis**\n*{current_time.strftime('%Y-%m-%d %H:%M UTC')}*\n\n"
        
        # Extract key topics with business focus
        topics = {
            "product": ["launch", "release", "announce", "new", "update", "feature"],
            "partnership": ["partner", "collaboration", "team", "join", "acquisition"],
            "research": ["research", "paper", "study", "breakthrough", "model"],
            "business": ["funding", "investment", "growth", "revenue", "enterprise"],
            "technical": ["api", "endpoint", "integration", "developer", "platform"]
        }
        
        categorized = {}
        for tweet in tweets:
            tweet_lower = tweet.lower()
            for category, keywords in topics.items():
                if any(keyword in tweet_lower for keyword in keywords):
                    if category not in categorized:
                        categorized[category] = []
                    categorized[category].append(tweet)
                    break
        
        # Generate business-focused summary
        if categorized:
            summary += "**Key Business Developments:**\n"
            for category, category_tweets in categorized.items():
                if category_tweets:
                    summary += f"• **{category.title()}**: {len(category_tweets)} significant updates detected\n"
            
            summary += f"\n**Activity Overview:**\n"
            summary += f"• Total significant posts analyzed: {len(tweets)}\n"
            summary += f"• Companies with notable activity: {len([c for c in categorized.values() if c])}\n"
            summary += f"• Time period: Last 5 business days\n"
        else:
            summary += "• Routine social media activity detected\n"
            summary += "• No major business developments identified\n"
            summary += f"• {len(tweets)} posts analyzed from monitored companies\n"
        
        summary += f"\n*Note: Manual analysis performed due to AI service unavailability. For detailed insights, AI-powered analysis will resume when service is restored.*"
        return summary
    def send_to_slack(self, message: str) -> bool:
        """Send summary to Slack"""
        webhook_url = os.getenv("SLACK_WEBHOOK_URL")
        if not webhook_url:
            logger.error("SLACK_WEBHOOK_URL not set")
            return False

        # Determine day of week for appropriate title
        current_time = datetime.now(timezone.utc)
        day_name = current_time.strftime('%A')
        
        payload = {
            "text": f"*📰 AI Business Week Summary - {day_name}, {current_time.strftime('%Y-%m-%d')}*\n\n{message}",
            "mrkdwn": True
        }

        try:
            response = requests.post(
                webhook_url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            if response.status_code == 200:
                logger.info("Successfully posted to Slack")
                return True
            else:
                logger.error(f"Slack API error: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            logger.error(f"Error posting to Slack: {e}")
            return False


async def main():
    """Main execution function"""
    # Check for required environment variables
    required_vars = ["SLACK_WEBHOOK_URL"]
    missing = [var for var in required_vars if not os.getenv(var)]
    if missing:
        logger.error(f"Missing environment variables: {', '.join(missing)}")
        return

    # Check for Scrapfly API key (optional but recommended)
    if not os.getenv("SCRAPFLY_API_KEY"):
        logger.warning("SCRAPFLY_API_KEY not found - will use Playwright fallback (less reliable)")
        logger.warning("For better results, sign up at https://scrapfly.io and add your API key to .env")

    if not SCRAPFLY_AVAILABLE and not PLAYWRIGHT_AVAILABLE:
        logger.error("Neither Scrapfly nor Playwright are available. Please install at least one:")
        logger.error("For Scrapfly: pip install scrapfly-sdk")
        logger.error("For Playwright: pip install playwright && playwright install chromium")
        return

    try:
        # Use the scraper with async context manager
        async with TwitterScraperNew() as scraper:
            # Scrape tweets from all accounts
            tweets = await scraper.scrape_all_accounts()
            
            # Generate summary
            if tweets:
                summary = scraper.generate_summary(tweets)
                message = f"{summary}\n\n_Scraped {len(tweets)} tweets from {len(X_ACCOUNTS)} AI companies (last 5 days)_"
            else:
                # More detailed failure message
                utc = timezone.utc
                current_time = datetime.now(utc)
                message = f"⚠️ **No Recent Tweets Found** - {current_time.strftime('%Y-%m-%d %H:%M UTC')}\n\n" \
                         f"The scraper checked all monitored AI companies but found no tweets from the last 5 days.\n\n" \
                         f"**Debug Info:**\n" \
                         f"- Checked: {', '.join(X_ACCOUNTS)}\n" \
                         f"- Time range: Last 120 hours from {current_time.strftime('%Y-%m-%d %H:%M UTC')}\n" \
                         f"- Scrapfly available: {'Yes' if SCRAPFLY_AVAILABLE else 'No'}\n" \
                         f"- Scrapfly key configured: {'Yes' if os.getenv('SCRAPFLY_API_KEY') else 'No'}\n" \
                         f"- Playwright available: {'Yes' if PLAYWRIGHT_AVAILABLE else 'No'}\n\n" \
                         f"**Possible causes:**\n" \
                         f"• Very quiet period across all companies (highly unlikely)\n" \
                         f"• X.com blocking or rate limiting our scraper\n" \
                         f"• Technical issues with scraping methods\n\n" \
                         f"The system will retry on the next scheduled run."            
            # Send to Slack
            if scraper.send_to_slack(message):
                logger.info("Successfully sent daily summary to Slack")
            else:
                logger.error("Failed to send summary to Slack")
                
    except Exception as e:
        logger.error(f"Critical error in main execution: {e}")
        
        # Try to send error notification to Slack
        try:
            error_payload = {
                "text": f"*⚠️ AI Summary Agent Error*\n\nThe daily scraper encountered an error:\n```{str(e)}```\n\nPlease check the logs for details.",
                "mrkdwn": True
            }
            webhook_url = os.getenv("SLACK_WEBHOOK_URL")
            if webhook_url:
                requests.post(webhook_url, json=error_payload, timeout=10)
        except:
            pass  # Don't let error notification failure crash the script

if __name__ == "__main__":
    asyncio.run(main())
