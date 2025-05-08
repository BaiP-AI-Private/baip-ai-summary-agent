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
from bs4 import BeautifulSoup
import pytz

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
    "dair_ai"
]

# List of Nitter instances (updated with more reliable ones)
NITTER_INSTANCES = [
    "https://nitter.net",
    "https://nitter.privacydev.net",
    "https://nitter.poast.org",
    "https://nitter.woodland.cafe",
    "https://nitter.weiler.rocks",
    "https://nitter.rawbit.ninja",
    "https://nitter.moomoo.me",
    "https://nitter.1d4.us",
    "https://nitter.kavin.rocks",
    "https://nitter.unixfox.eu",
    "https://nitter.42l.fr",
    "https://nitter.nixnet.services",
    "https://nitter.fdn.fr",
    "https://nitter.40two.app",
    "https://nitter.mint.lgbt"
]

class TwitterScraper:
    def __init__(self):
        self.available_instances = [
            "https://nitter.net",
            "https://nitter.1d4.us",
            "https://nitter.kavin.rocks",
            "https://nitter.unixfox.eu",
            "https://nitter.moomoo.me",
            "https://nitter.privacydev.net",
            "https://nitter.poast.org",
            "https://nitter.mint.lgbt",
            "https://nitter.woodland.cafe",
            "https://nitter.weiler.rocks"
        ]
        self.current_instance = None
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0'
        })
        self.session.verify = True
        self.session.allow_redirects = True
        self.session.timeout = 30
        self.tried_instances = set()
        
    def check_instance_availability(self, instance):
        """Check if a Nitter instance is available"""
        try:
            response = self.session.get(
                f"{instance}/OpenAI",
                timeout=5,
                verify=False,
                allow_redirects=True
            )
            if response.status_code == 200:
                # Check if the response actually contains tweet content
                soup = BeautifulSoup(response.text, 'html.parser')
                tweet_containers = soup.find_all('div', class_='tweet-content')
                return len(tweet_containers) > 0
            return False
        except:
            return False

    def get_available_instances(self):
        """Get list of available Nitter instances"""
        available = []
        for instance in self.available_instances:
            if self.check_instance_availability(instance):
                available.append(instance)
                logger.info(f"Found available Nitter instance: {instance}")
        return available
    
    def get_user_tweets(self, username, start_date, end_date):
        """Get tweets from a user within date range"""
        tweets = []
        page = 1
        max_pages = 10  # Limit to 10 pages per account
        
        while page <= max_pages:
            try:
                # Construct URL with proper path
                url = f"{self.current_instance}/{username}"
                if page > 1:
                    url += f"?page={page}"
                
                logger.info(f"Fetching from URL: {url} (Page {page}/{max_pages})")
                
                response = self.session.get(url, timeout=30)
                if response.status_code != 200:
                    logger.error(f"Failed to fetch tweets for {username}: {response.status_code}")
                    break
                
                soup = BeautifulSoup(response.text, 'html.parser')
                tweet_containers = soup.find_all('div', class_='timeline-item')
                
                if not tweet_containers:
                    logger.warning(f"No tweets found on page {page} for {username}")
                    break
                
                logger.info(f"Found {len(tweet_containers)} tweet containers on page {page}")
                
                for container in tweet_containers:
                    try:
                        # Find tweet text
                        tweet_text = container.find('div', class_='tweet-content')
                        if not tweet_text:
                            continue
                        
                        # Find tweet date
                        date_element = container.find('span', class_='tweet-date')
                        if not date_element:
                            continue
                            
                        date_str = date_element.find('a')['title']
                        logger.debug(f"Found tweet date: {date_str}")
                        
                        # Parse date
                        try:
                            tweet_date = datetime.strptime(date_str, '%b %d, %Y · %I:%M %p UTC')
                            tweet_date = pytz.UTC.localize(tweet_date)
                        except ValueError:
                            try:
                                tweet_date = datetime.strptime(date_str, '%b %d, %Y · %H:%M UTC')
                                tweet_date = pytz.UTC.localize(tweet_date)
                            except ValueError:
                                logger.warning(f"Could not parse date: {date_str}")
                                continue
                        
                        # Check if tweet is within date range
                        if start_date <= tweet_date <= end_date:
                            tweet_text = tweet_text.get_text(strip=True)
                            tweets.append(f"@{username}: {tweet_text}")
                            logger.info(f"Found tweet from {username} at {tweet_date}")
                        else:
                            logger.debug(f"Tweet from {tweet_date} outside date range")
                            
                    except Exception as e:
                        logger.error(f"Error parsing tweet: {e}")
                        continue
                
                # Check if we need to continue to next page
                if len(tweet_containers) < 20:  # Nitter shows 20 tweets per page
                    break
                    
                page += 1
                time.sleep(random.uniform(2, 4))  # Random delay between pages
                
            except Exception as e:
                logger.error(f"Error fetching tweets for {username}: {e}")
                break
        
        logger.info(f"Found {len(tweets)} tweets for {username}")
        if not tweets:
            logger.warning(f"No tweets found for {username} in the last 24 hours")
        return tweets

def get_date_range():
    """Get date range for the last 24 hours in UTC"""
    utc = pytz.UTC
    end = datetime.now(utc)
    start = end - timedelta(days=1)
    
    # Log the actual dates being used
    logger.info(f"Current UTC time: {end}")
    logger.info(f"Start date: {start}")
    logger.info(f"End date: {end}")
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
    
    try:
        # Initialize scraper
        scraper = TwitterScraper()
        if not scraper.session:
            logger.error("Failed to initialize scraper session")
            return
        
        # Get date range
        start_date, end_date = get_date_range()
        logger.info(f"Fetching tweets from {start_date} to {end_date}")
        
        # Scrape tweets
        all_tweets = []
        for account in AI_ACCOUNTS:
            logger.info(f"Processing {account}...")
            tweets = scraper.get_user_tweets(account, start_date, end_date)
            if tweets:
                logger.info(f"Found {len(tweets)} tweets from {account}")
                all_tweets.extend(tweets)
            else:
                logger.warning(f"No tweets found for {account} in the last 24 hours")
            
            time.sleep(random.uniform(3, 5))  # Rate limiting
        
        if not all_tweets:
            logger.warning("No tweets found from any account in the last 24 hours")
            return
            
        # Generate and send summary
        summary = generate_summary(all_tweets)
        logger.info("\nGenerated Summary:\n" + summary)
        
        if not send_to_slack(summary):
            logger.error("Failed to send summary to Slack")
    except Exception as e:
        logger.error(f"Critical error in main execution: {e}")
        raise

if __name__ == "__main__":
    main()
