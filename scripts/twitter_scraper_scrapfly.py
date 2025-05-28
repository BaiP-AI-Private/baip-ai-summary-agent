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

# Try to import playwright
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
        logging.FileHandler('../tweet_scraper.log'),
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

    async def scrape_user_timeline(self, username: str, max_tweets: int = 10) -> List[Dict]:
        """Scrape recent tweets from a user's timeline"""
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

    def is_tweet_from_yesterday(self, tweet: Dict) -> bool:
        """Check if tweet is from yesterday (previous 24 hours)"""
        try:
            created_at = tweet.get("created_at")
            if not created_at:
                return False
            
            # Parse Twitter's date format: "Wed Oct 10 20:19:24 +0000 2018"
            tweet_date = datetime.strptime(created_at, "%a %b %d %H:%M:%S %z %Y")
            
            # Get yesterday's date range in UTC
            utc = timezone.utc
            now = datetime.now(utc)
            yesterday_start = (now - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
            yesterday_end = (now - timedelta(days=1)).replace(hour=23, minute=59, second=59, microsecond=999999)
            
            return yesterday_start <= tweet_date <= yesterday_end
            
        except Exception as e:
            logger.error(f"Error parsing tweet date: {e}")
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
        """Scrape tweets from all configured accounts"""
        all_tweets = []
        successful_accounts = 0
        
        for username in X_ACCOUNTS:
            try:
                logger.info(f"Processing @{username}...")
                tweets = await self.scrape_user_timeline(username, max_tweets=20)
                
                # Filter to yesterday's tweets
                yesterday_tweets = [t for t in tweets if self.is_tweet_from_yesterday(t)]
                
                if yesterday_tweets:
                    for tweet in yesterday_tweets[:5]:  # Limit to 5 tweets per account
                        formatted_tweet = self.format_tweet_for_summary(tweet, username)
                        all_tweets.append(formatted_tweet)
                    
                    logger.info(f"Found {len(yesterday_tweets)} relevant tweets from @{username}")
                    successful_accounts += 1
                else:
                    logger.info(f"No yesterday tweets found for @{username}")
                
                # Rate limiting
                await asyncio.sleep(2)
                
            except Exception as e:
                logger.error(f"Failed to process @{username}: {e}")
                continue
        
        logger.info(f"Successfully processed {successful_accounts}/{len(X_ACCOUNTS)} accounts")
        logger.info(f"Total tweets collected: {len(all_tweets)}")
        
        return all_tweets

    def generate_summary(self, tweets: List[str]) -> str:
        """Generate AI summary of tweets"""
        if not tweets:
            return "No tweets found from monitored AI companies in the last 24 hours."
        
        # Combine tweets for analysis
        tweets_text = "\n\n".join(tweets[:25])  # Limit to prevent token overflow
        
        prompt = f"""Analyze these tweets from AI companies and create a concise daily summary:

Key points to extract:
- New product announcements
- Technical breakthroughs
- Important partnerships
- Notable research findings
- Significant company updates
- Industry trends and insights

Please format the summary in clear bullet points with the most important information first.

Tweets from the last 24 hours:
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
        """Generate a manual summary when AI is unavailable"""
        summary = "**Daily AI Summary - Manual Overview**\n\n"
        
        # Extract key topics
        topics = {
            "model": ["gpt", "claude", "gemini", "llama", "mistral", "model"],
            "api": ["api", "endpoint", "integration", "developer"],
            "research": ["research", "paper", "study", "breakthrough"],
            "product": ["launch", "release", "announce", "new", "update"],
            "partnership": ["partner", "collaboration", "team", "join"]
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
        
        if categorized:
            for category, category_tweets in categorized.items():
                if category_tweets:
                    summary += f"• **{category.title()} Updates**: {len(category_tweets)} related posts\n"
        
        summary += "\n**Sample Posts:**\n"
        for tweet in tweets[:8]:
            summary += f"• {tweet}\n"
        
        summary += "\n*Manual summary generated - AI analysis unavailable*"
        return summary
    def send_to_slack(self, message: str) -> bool:
        """Send summary to Slack"""
        webhook_url = os.getenv("SLACK_WEBHOOK_URL")
        if not webhook_url:
            logger.error("SLACK_WEBHOOK_URL not set")
            return False

        payload = {
            "text": f"*📰 Daily AI Summary - {datetime.now().strftime('%Y-%m-%d')}*\n\n{message}",
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

    if not PLAYWRIGHT_AVAILABLE:
        logger.error("Playwright is not available. Please install it:")
        logger.error("pip install playwright")
        logger.error("playwright install chromium")
        return

    try:
        # Use the scraper with async context manager
        async with TwitterScraperNew() as scraper:
            # Scrape tweets from all accounts
            tweets = await scraper.scrape_all_accounts()
            
            # Generate summary
            if tweets:
                summary = scraper.generate_summary(tweets)
                message = f"{summary}\n\n_Scraped {len(tweets)} tweets from {len(X_ACCOUNTS)} AI companies_"
            else:
                message = "No tweets found from monitored AI companies in the last 24 hours. All accounts were checked but no recent activity was detected."            
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
