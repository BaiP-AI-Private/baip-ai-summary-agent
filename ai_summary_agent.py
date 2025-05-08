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
# AI_ACCOUNTS = ["elonmusk"]

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
        # Use the global NITTER_INSTANCES variable
        self.available_instances = NITTER_INSTANCES
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
        self.instance_retry_delays = {}  # Track retry delays for each instance

        # Initialize with a working instance
        self.current_instance = self.get_working_instance()
        if not self.current_instance:
            raise Exception("No working Nitter instances found")  # Added missing exception
        logger.info(f"Using Nitter instance: {self.current_instance}")
    
    def get_working_instance(self):
        """Get a working Nitter instance"""
        for instance in self.available_instances:
            try:
                # Check if instance is in cooldown
                if instance in self.instance_retry_delays:
                    delay = self.instance_retry_delays[instance]
                    if datetime.now() < delay:
                        logger.debug(f"Instance {instance} in cooldown until {delay}")
                        continue
                
                response = self.session.get(f"{instance}/OpenAI", timeout=10)
                # Check if we're redirected to health check page
                if "status.d420.de" in response.url:
                    logger.warning(f"Instance {instance} redirected to health check page, skipping")
                    continue
                    
                if response.status_code == 200:
                    logger.info(f"Found working Nitter instance: {instance}")
                    return instance
                elif response.status_code == 429:
                    # Set cooldown for rate-limited instance (1.5 minutes)
                    cooldown = datetime.now() + timedelta(seconds=90)
                    self.instance_retry_delays[instance] = cooldown
                    logger.warning(f"Instance {instance} rate limited, cooling down until {cooldown}")
            except Exception as e:
                logger.debug(f"Instance {instance} not working: {e}")
                continue
            time.sleep(5)  # Added delay between retries
        return None

    def get_user_tweets(self, username, start_date, end_date):
        """Get tweets from a user within date range"""
        tweets = []
        retry_count = 0
        max_retries = 3
        last_working_instance = None
        load_more_url = None  # URL for loading more tweets
        load_more_clicks = 0  # Track number of load more clicks
        max_load_more_clicks = 5  # Maximum number of load more clicks to simulate
        found_tweets_in_range = False  # Initialize at the start

        while retry_count < max_retries:
            try:
                # Use last working instance if available and not in cooldown
                if last_working_instance and last_working_instance not in self.instance_retry_delays:
                    self.current_instance = last_working_instance
                else:
                    # Get a new instance only if needed
                    self.current_instance = self.get_working_instance()
                    if not self.current_instance:
                        logger.error("No working Nitter instances available")
                        break
                    time.sleep(5)  # Wait before trying new instance

                # Construct the initial URL or use the "Load more" URL
                base_url = f"{self.current_instance}/{username}"
                url = load_more_url if load_more_url else base_url
                logger.info(f"Fetching from URL: {url}")

                response = self.session.get(url, timeout=30)
                # Check if we're redirected to health check page
                if "status.d420.de" in response.url:
                    logger.warning(f"Instance {self.current_instance} redirected to health check page, trying another instance")
                    self.current_instance = self.get_working_instance()
                    if not self.current_instance:
                        retry_count += 1
                        time.sleep(30 * (2 ** retry_count))  # Exponential backoff
                        continue
                    time.sleep(5)  # Wait before trying new instance
                    continue

                if response.status_code == 429:
                    logger.warning(f"Rate limited by {self.current_instance}")
                    # Set cooldown for current instance (1.5 minutes)
                    cooldown = datetime.now() + timedelta(seconds=90)
                    self.instance_retry_delays[self.current_instance] = cooldown
                    # Try another instance
                    self.current_instance = self.get_working_instance()
                    if not self.current_instance:
                        retry_count += 1
                        time.sleep(30 * (2 ** retry_count))  # Exponential backoff
                        continue
                    time.sleep(5)  # Wait before trying new instance
                    continue
                elif response.status_code != 200:
                    logger.error(f"Failed to fetch tweets for {username}: {response.status_code}")
                    # Try another instance
                    self.current_instance = self.get_working_instance()
                    if not self.current_instance:
                        retry_count += 1
                        time.sleep(30 * (2 ** retry_count))  # Exponential backoff
                        continue
                    time.sleep(5)  # Wait before trying new instance
                    continue

                # If we get here, the instance is working
                last_working_instance = self.current_instance

                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Debug: Print the HTML to see what we're getting
                logger.debug(f"Page HTML: {soup.prettify()[:1000]}")  # Print first 1000 chars for debugging
                
                # Debug: Print all div classes to see what's available
                all_divs = soup.find_all('div', class_=True)
                logger.debug("Found divs with classes:")
                for div in all_divs:
                    logger.debug(f"Div class: {div.get('class')}")
                
                # Find all tweet containers first
                tweet_containers = soup.find_all('div', class_='timeline-item')
                logger.debug(f"Found {len(tweet_containers)} timeline-item containers")
                
                if not tweet_containers:
                    tweet_containers = soup.find_all('div', class_='thread-line')
                    logger.debug(f"Found {len(tweet_containers)} thread-line containers")
                    
                    if not tweet_containers:
                        # Try alternative class names
                        tweet_containers = soup.find_all('div', class_='tweet-body')
                        logger.debug(f"Found {len(tweet_containers)} tweet-body containers")
                        
                        if not tweet_containers:
                            tweet_containers = soup.find_all('div', class_='tweet')
                            logger.debug(f"Found {len(tweet_containers)} tweet containers")

                if tweet_containers:
                    logger.info(f"Found {len(tweet_containers)} tweet containers")
                    
                    for container in tweet_containers:
                        try:
                            # Find tweet text - look for the tweet-content div
                            tweet_text_div = container.find('div', class_='tweet-content')
                            if not tweet_text_div:
                                # Try alternative class names
                                tweet_text_div = container.find('div', class_='tweet-body')
                                if not tweet_text_div:
                                    continue

                            # Find tweet date - look for the tweet-date span
                            date_element = container.find('span', class_='tweet-date')
                            if not date_element:
                                # Try alternative class names
                                date_element = container.find('a', class_='tweet-date')
                                if not date_element:
                                    continue

                            # Get the date from the title attribute of the link
                            date_link = date_element.find('a') if date_element.name != 'a' else date_element
                            if not date_link or 'title' not in date_link.attrs:
                                continue

                            date_str = date_link['title']
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
                                tweet_text = tweet_text_div.get_text(strip=True)
                                tweets.append(f"@{username}: {tweet_text}")
                                logger.info(f"Found tweet from {username} at {tweet_date}")
                                found_tweets_in_range = True
                            else:
                                logger.debug(f"Tweet from {tweet_date} outside date range {start_date} to {end_date}")

                        except Exception as e:
                            logger.error(f"Error parsing tweet: {e}")
                            continue
                else:
                    logger.warning(f"No tweets found for {username} on this page.")

                # Find the "show-more" button and get its URL
                show_more = soup.find('div', class_='show-more')
                logger.debug(f"Show more div found: {show_more}")
                
                if show_more:
                    show_more_link = show_more.find('a')
                    logger.debug(f"Show more link found: {show_more_link}")
                    
                    if show_more_link and 'href' in show_more_link.attrs:
                        cursor = show_more_link['href']
                        logger.debug(f"Found cursor: {cursor}")
                        
                        if cursor.startswith('?'):
                            load_more_url = f"{base_url}{cursor}"
                        else:
                            load_more_url = f"{base_url}?{cursor}"
                        logger.info(f"Found 'show-more' URL with cursor: {load_more_url}")
                        
                        if load_more_clicks < max_load_more_clicks:
                            load_more_clicks += 1
                            logger.info(f"Simulating load more click {load_more_clicks} of {max_load_more_clicks}")
                            time.sleep(random.uniform(5, 10))  # Delay before loading more tweets
                            continue
                    else:
                        logger.warning("Show more element found but missing href attribute")
                        if show_more_link:
                            logger.debug(f"Show more element attributes: {show_more_link.attrs}")
                else:
                    load_more_url = None
                    if load_more_clicks >= max_load_more_clicks:
                        logger.info(f"Reached maximum load more clicks ({max_load_more_clicks})")
                    else:
                        logger.info("No 'show-more' button found, assuming last page")

                # If we've processed all tweets and haven't found any in range, and there's no more content, break
                if not found_tweets_in_range and not load_more_url:
                    break

            except Exception as e:
                logger.error(f"Error fetching tweets for {username}: {e}")
                retry_count += 1
                if retry_count >= max_retries:
                    logger.error(f"Max retries reached for {username}")
                    break
                time.sleep(30 * (2 ** retry_count))  # Exponential backoff
                continue

        logger.info(f"Found {len(tweets)} tweets for {username}")
        if not tweets:
            logger.warning(f"No tweets found for {username} in the last 24 hours")
        return tweets

def get_date_range():
    """Get date range for the previous day in UTC (00:00 to 23:59)"""
    utc = pytz.UTC
    now = datetime.now(utc)
    
    # Set end date to yesterday at 23:59:59
    end = datetime(now.year, now.month, now.day, 23, 59, 59, tzinfo=utc) - timedelta(days=1)
    # Set start date to yesterday at 00:00:00
    start = datetime(now.year, now.month, now.day, 0, 0, 0, tzinfo=utc) - timedelta(days=1)
    
    # Log the actual dates being used
    logger.info(f"Current UTC time: {now}")
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
