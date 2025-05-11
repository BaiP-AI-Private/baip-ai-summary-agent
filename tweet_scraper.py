import os
import json
import openai
import requests
import logging
from datetime import datetime, timedelta
from dotenv import load_dotenv
import time
import random
from bs4 import BeautifulSoup
import pytz

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
openai.api_key = os.getenv("OPENAI_API_KEY")

# Configuration
X_ACCOUNTS = [
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

class TweetScraper:
    def __init__(self):
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
        self.instance_retry_delays = {}
        self.current_instance = self._get_working_instance()
        if not self.current_instance:
            raise Exception("No working Nitter instances found")
        logger.info(f"Using Nitter instance: {self.current_instance}")

    def _get_working_instance(self):
        """Get a working Nitter instance"""
        for instance in NITTER_INSTANCES:
            try:
                if instance in self.instance_retry_delays:
                    delay = self.instance_retry_delays[instance]
                    if datetime.now() < delay:
                        logger.debug(f"Instance {instance} in cooldown until {delay}")
                        continue

                response = self.session.get(f"{instance}/OpenAI", timeout=10)
                if "status.d420.de" in response.url:
                    logger.warning(f"Instance {instance} redirected to health check page, skipping")
                    continue

                if response.status_code == 200:
                    logger.info(f"Found working Nitter instance: {instance}")
                    return instance
                elif response.status_code == 429:
                    cooldown = datetime.now() + timedelta(seconds=90)
                    self.instance_retry_delays[instance] = cooldown
                    logger.warning(f"Instance {instance} rate limited, cooling down until {cooldown}")
            except Exception as e:
                logger.debug(f"Instance {instance} not working: {e}")
                continue
            time.sleep(5)
        return None

    def _get_date_range(self):
        """Get date range for the previous day in UTC"""
        utc = pytz.UTC
        now = datetime.now(utc)
        end = datetime(now.year, now.month, now.day, 23, 59, 59, tzinfo=utc) - timedelta(days=1)
        start = datetime(now.year, now.month, now.day, 0, 0, 0, tzinfo=utc) - timedelta(days=1)
        logger.info(f"Current UTC time: {now}")
        logger.info(f"Start date: {start}")
        logger.info(f"End date: {end}")
        return start, end

    def _parse_tweet_date(self, date_str):
        """Parse tweet date from various formats"""
        try:
            tweet_date = datetime.strptime(date_str, '%b %d, %Y · %I:%M %p UTC')
            return pytz.UTC.localize(tweet_date)
        except ValueError:
            try:
                tweet_date = datetime.strptime(date_str, '%b %d, %Y · %H:%M UTC')
                return pytz.UTC.localize(tweet_date)
            except ValueError:
                logger.warning(f"Could not parse date: {date_str}")
                return None

    def get_user_tweets(self, username, start_date, end_date):
        """Get tweets from a user within date range"""
        tweets = []
        load_more_url = None
        load_more_clicks = 0
        max_load_more_clicks = 5

        while load_more_clicks < max_load_more_clicks:
            try:
                url = load_more_url if load_more_url else f"{self.current_instance}/{username}"
                logger.info(f"Fetching from URL: {url}")

                response = self.session.get(url, timeout=30)
                
                if response.status_code != 200:
                    logger.error(f"Failed to fetch tweets for {username}: {response.status_code}")
                    self.current_instance = self._get_working_instance()
                    if not self.current_instance:
                        break
                    time.sleep(5)
                    continue

                soup = BeautifulSoup(response.text, 'html.parser')
                
                # ADDED: Debug log to see what HTML we're getting
                logger.debug(f"Page title: {soup.title.string if soup.title else 'No title'}")
                
                tweet_containers = soup.find_all('div', class_='timeline-item')
                
                if not tweet_containers:
                    # Log more detailed info and try alternative selectors
                    logger.warning(f"No tweets found for {username} on this page using standard selector")
                    
                    # Try alternative selectors that might be used by Nitter
                    alt_containers = soup.find_all('div', class_='tweet')
                    if alt_containers:
                        logger.info(f"Found {len(alt_containers)} tweets using alternative selector")
                        tweet_containers = alt_containers
                    else:
                        # Log a sample of the HTML to debug
                        logger.debug(f"HTML excerpt: {soup.prettify()[0:500]}...")
                        break

                logger.info(f"Found {len(tweet_containers)} tweet containers")
                
                for container in tweet_containers:
                    try:
                        tweet_text_div = container.find('div', class_='tweet-content')
                        date_element = container.find('span', class_='tweet-date')
                        
                        if not tweet_text_div or not date_element:
                            continue

                        date_link = date_element.find('a')
                        if not date_link or 'title' not in date_link.attrs:
                            continue

                        tweet_date = self._parse_tweet_date(date_link['title'])
                        if not tweet_date:
                            continue

                        if start_date <= tweet_date <= end_date:
                            tweet_text = tweet_text_div.get_text(strip=True)
                            tweets.append(f"@{username}: {tweet_text}")
                            logger.info(f"Found tweet from {username} at {tweet_date}")

                    except Exception as e:
                        logger.error(f"Error parsing tweet: {e}")
                        continue

                # Handle pagination
                show_more = soup.find('div', class_='show-more')
                if show_more:
                    show_more_link = show_more.find('a')
                    if show_more_link and 'href' in show_more_link.attrs:
                        cursor = show_more_link['href']
                        if cursor.startswith('?'):
                            cursor = cursor[1:]
                        load_more_url = f"{self.current_instance}/{username}?{cursor}"
                        load_more_clicks += 1
                        logger.info(f"Found more tweets, clicking load more ({load_more_clicks}/{max_load_more_clicks})")
                        time.sleep(random.uniform(5, 10))
                        continue
                break

            except Exception as e:
                logger.error(f"Error fetching tweets for {username}: {e}")
                break

        logger.info(f"Found {len(tweets)} tweets for {username}")
        return tweets

    def generate_summary(self, tweets):
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

    def send_to_slack(self, message):
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
                headers={"Content-Type": "application/json"}
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
        scraper = TweetScraper()
        
        # Get date range
        start_date, end_date = scraper._get_date_range()
        logger.info(f"Fetching tweets from {start_date} to {end_date}")
        
        # Scrape tweets
        all_tweets = []
        for account in X_ACCOUNTS:
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
        summary = scraper.generate_summary(all_tweets)
        logger.info("\nGenerated Summary:\n" + summary)
        
        if not scraper.send_to_slack(summary):
            logger.error("Failed to send summary to Slack")
    except Exception as e:
        logger.error(f"Critical error in main execution: {e}")
        raise

if __name__ == "__main__":
    main() 