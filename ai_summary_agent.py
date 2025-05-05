import os
import json
import openai
import requests
import certifi
from datetime import datetime, timedelta
from dotenv import load_dotenv
import time
import random
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

# Configuration
AI_ACCOUNTS = [
    "OpenAI",
    "xai",
    "AnthropicAI",
    "GoogleDeepMind",
    "MistralAI",
    "AIatMeta",
    "Cohere",
    "perplexity_ai",
    "scale_ai",
    "runwayml",
    "AnthropicAI",
    "dair_ai"
]

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
]

TWITTER_AUTH_TOKEN = "AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs%3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA"

class TwitterScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.verify = certifi.where()
        self.setup_session()
        
    def setup_session(self):
        """Initialize session with headers and authentication"""
        self.session.headers.update({
            "User-Agent": random.choice(USER_AGENTS),
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.9",
            "Origin": "https://twitter.com",
            "Referer": "https://twitter.com/",
            "Authorization": f"Bearer {TWITTER_AUTH_TOKEN}",
        })
        self.activate_guest_token()
        
    def activate_guest_token(self):
        """Get and set guest token for session"""
        try:
            response = self.session.post("https://api.twitter.com/1.1/guest/activate.json")
            if response.status_code == 200:
                guest_token = response.json().get("guest_token")
                self.session.headers.update({"x-guest-token": guest_token})
                logger.info("Successfully obtained guest token")
                return True
        except Exception as e:
            logger.error(f"Error getting guest token: {e}")
        return False
    
    def get_user_id(self, username):
        """Get Twitter user ID from username"""
        params = {
            "variables": json.dumps({"screen_name": username, "withHighlightedLabel": True})
        }
        try:
            response = self.session.get(
                "https://twitter.com/i/api/graphql/4S2ihIKfF3xhp-ENxvUAfQ/UserByScreenName",
                params=params
            )
            if response.status_code == 200:
                data = response.json()
                return data.get("data", {}).get("user", {}).get("rest_id")
        except Exception as e:
            logger.error(f"Error getting user ID for {username}: {e}")
        return None
    
    def get_user_tweets(self, user_id, start_date, end_date, limit=10):
        """Fetch user tweets within date range"""
        variables = {
            "userId": user_id,
            "count": limit,
            "includePromotedContent": False,
            "withVoice": True,
            "withV2Timeline": True
        }
        
        features = {
            "responsive_web_graphql_timeline_navigation_enabled": True,
            "responsive_web_graphql_skip_user_profile_image_extensions_enabled": False,
        }
        
        params = {
            "variables": json.dumps(variables),
            "features": json.dumps(features)
        }
        
        try:
            response = self.session.get(
                "https://twitter.com/i/api/graphql/zICd6x_warY0bzMRm-piIg/UserTweets",
                params=params
            )
            
            if response.status_code == 200:
                return self.parse_tweets(response.json(), start_date, end_date)
        except Exception as e:
            logger.error(f"Error fetching tweets: {e}")
        return []
    
    def parse_tweets(self, data, start_date, end_date):
        """Parse tweets from API response"""
        tweets = []
        instructions = data.get("data", {}).get("user", {}).get("result", {}).get("timeline_v2", {}).get("timeline", {}).get("instructions", [])
        
        for instruction in instructions:
            if instruction.get("type") == "TimelineAddEntries":
                for entry in instruction.get("entries", []):
                    content = entry.get("content", {})
                    if "itemContent" in content and "tweet_results" in content["itemContent"]:
                        tweet = content["itemContent"]["tweet_results"].get("result", {})
                        if "legacy" in tweet:
                            try:
                                tweet_date = datetime.strptime(tweet["legacy"]["created_at"], "%a %b %d %H:%M:%S %z %Y")
                                if start_date <= tweet_date <= end_date:
                                    tweets.append(tweet["legacy"]["full_text"])
                            except Exception as e:
                                logger.error(f"Error parsing tweet date: {e}")
        return tweets

def get_date_range():
    """Get yesterday's date range in UTC"""
    yesterday = datetime.utcnow() - timedelta(days=1)
    start = yesterday.replace(hour=0, minute=0, second=0, microsecond=0)
    end = yesterday.replace(hour=23, minute=59, second=59, microsecond=0)
    return start, end

def generate_summary(tweets):
    """Generate summary using OpenAI"""
    if not tweets:
        return "No tweets found from monitored accounts in the last 24 hours."
    
    text = "\n\n".join(tweets[:20])  # Limit to first 20 tweets
    prompt = """Analyze these tweets from AI companies and create a concise daily summary:
    
Key points to extract:
- New product announcements
- Technical breakthroughs
- Important partnerships
- Notable research findings
- Significant company updates

Tweets:
{}

Summary (in bullet points):""".format(text)
    
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=500
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"Error generating summary: {e}")
        return "Failed to generate summary"

def send_to_slack(message):
    """Send summary to Slack"""
    webhook_url = os.getenv("SLACK_WEBHOOK_URL")
    if not webhook_url:
        logger.error("SLACK_WEBHOOK_URL not set")
        return False
    
    payload = {
        "text": f"*📰 Daily AI Summary - {datetime.utcnow().strftime('%Y-%m-%d')}*\n\n{message}",
        "mrkdwn": True
    }
    
    try:
        response = requests.post(
            webhook_url,
            json=payload,
            headers={"Content-Type": "application/json"},
            verify=certifi.where()
        )
        if response.status_code == 200:
            logger.info("Successfully posted to Slack")
            return True
        logger.error(f"Slack API error: {response.status_code} - {response.text}")
    except Exception as e:
        logger.error(f"Error posting to Slack: {e}")
    return False

def main():
    """Main execution flow"""
    # Validate environment variables
    required_vars = ["OPENAI_API_KEY", "SLACK_WEBHOOK_URL"]
    missing = [var for var in required_vars if not os.getenv(var)]
    if missing:
        logger.error(f"Missing environment variables: {', '.join(missing)}")
        return
    
    # Initialize scraper
    scraper = TwitterScraper()
    if not scraper.session.headers.get("x-guest-token"):
        logger.error("Failed to initialize Twitter session")
        return
    
    # Get date range
    start_date, end_date = get_date_range()
    logger.info(f"Fetching tweets from {start_date.date()} to {end_date.date()}")
    
    # Scrape tweets
    all_tweets = []
    for account in AI_ACCOUNTS:
        logger.info(f"Processing {account}...")
        user_id = scraper.get_user_id(account)
        if not user_id:
            logger.warning(f"Could not find user ID for {account}")
            continue
        
        tweets = scraper.get_user_tweets(user_id, start_date, end_date)
        if tweets:
            logger.info(f"Found {len(tweets)} tweets from {account}")
            all_tweets.extend(tweets)
        
        time.sleep(random.uniform(1, 3))  # Rate limiting
    
    # Generate and send summary
    summary = generate_summary(all_tweets)
    logger.info("\nGenerated Summary:\n" + summary)
    
    if not send_to_slack(summary):
        logger.error("Failed to send summary to Slack")

if __name__ == "__main__":
    main()
