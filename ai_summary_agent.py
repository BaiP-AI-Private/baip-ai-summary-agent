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

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.81 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.81 Safari/537.36"
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
    "https://nitter.unixfox.eu"
]

class TwitterScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.verify = certifi.where()
        self.setup_session()
        self.available_instances = self.get_available_instances()
        if not self.available_instances:
            raise Exception("No available Nitter instances found")
        self.current_instance = random.choice(self.available_instances)
        self.tried_instances = set()
        
    def setup_session(self):
        """Initialize session with headers"""
        self.session.headers.update({
            "User-Agent": random.choice(USER_AGENTS),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        })
        return True

    def check_instance_availability(self, instance):
        """Check if a Nitter instance is available"""
        try:
            response = self.session.get(f"{instance}/OpenAI", timeout=5, verify=False)
            return response.status_code == 200
        except:
            return False

    def get_available_instances(self):
        """Get list of available Nitter instances"""
        available = []
        for instance in NITTER_INSTANCES:
            if self.check_instance_availability(instance):
                available.append(instance)
                logger.info(f"Found available Nitter instance: {instance}")
        return available
    
    def get_user_tweets(self, username, start_date, end_date, limit=10):
        """Fetch user tweets within date range"""
        tweets = []
        page = 1
        
        while len(tweets) < limit and len(self.tried_instances) < len(self.available_instances):
            try:
                url = f"{self.current_instance}/{username}"
                if page > 1:
                    url += f"?page={page}"
                
                logger.info(f"Fetching from URL: {url}")
                
                # Try with SSL verification first
                try:
                    response = self.session.get(url, timeout=10)
                except requests.exceptions.SSLError:
                    # If SSL verification fails, try without verification
                    logger.warning(f"SSL verification failed for {self.current_instance}, trying without verification")
                    response = self.session.get(url, verify=False, timeout=10)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    tweet_containers = soup.find_all('div', class_='tweet-content')
                    
                    if not tweet_containers:
                        logger.warning(f"No tweets found on page {page} for {username}")
                        # Try another instance if no tweets found
                        self.tried_instances.add(self.current_instance)
                        remaining_instances = [i for i in self.available_instances if i not in self.tried_instances]
                        if remaining_instances:
                            self.current_instance = random.choice(remaining_instances)
                            continue
                        break
                    
                    logger.info(f"Found {len(tweet_containers)} tweet containers on page {page}")
                    
                    for container in tweet_containers:
                        try:
                            tweet_text = container.get_text(strip=True)
                            tweet_time_element = container.find_previous('span', class_='tweet-date')
                            if not tweet_time_element:
                                logger.warning("Could not find tweet date element")
                                continue
                                
                            tweet_time = tweet_time_element.find('a')['title']
                            logger.info(f"Found tweet with time: {tweet_time}")
                            
                            # Try different date formats
                            try:
                                tweet_date = datetime.strptime(tweet_time, '%b %d, %Y · %I:%M %p UTC')
                            except ValueError:
                                try:
                                    tweet_date = datetime.strptime(tweet_time, '%b %d, %Y · %H:%M UTC')
                                except ValueError:
                                    logger.warning(f"Could not parse tweet date: {tweet_time}")
                                    continue
                            
                            logger.info(f"Parsed tweet date: {tweet_date}")
                            logger.info(f"Date range: {start_date} to {end_date}")
                            
                            if start_date <= tweet_date <= end_date:
                                tweets.append(tweet_text)
                                logger.info(f"Added tweet: {tweet_text[:50]}...")
                                if len(tweets) >= limit:
                                    break
                            else:
                                logger.info(f"Tweet date {tweet_date} outside range {start_date} to {end_date}")
                                
                        except Exception as e:
                            logger.warning(f"Error parsing tweet: {e}")
                            continue
                    
                    page += 1
                    time.sleep(random.uniform(1, 2))  # Rate limiting
                else:
                    logger.error(f"Failed to fetch tweets for {username}: Status {response.status_code}")
                    self.tried_instances.add(self.current_instance)
                    remaining_instances = [i for i in self.available_instances if i not in self.tried_instances]
                    if remaining_instances:
                        self.current_instance = random.choice(remaining_instances)
                        time.sleep(random.uniform(2, 4))  # Longer delay after error
                        continue
                    break
                    
            except requests.exceptions.RequestException as e:
                logger.error(f"Error fetching tweets for {username}: {e}")
                self.tried_instances.add(self.current_instance)
                remaining_instances = [i for i in self.available_instances if i not in self.tried_instances]
                if remaining_instances:
                    self.current_instance = random.choice(remaining_instances)
                    time.sleep(random.uniform(2, 4))  # Longer delay after error
                    continue
                break
            except Exception as e:
                logger.error(f"Unexpected error for {username}: {e}")
                break
        
        logger.info(f"Found {len(tweets)} tweets for {username}")
        return tweets

def get_date_range():
    """Get date range for the last 24 hours in UTC"""
    end = datetime.utcnow()
    start = end - timedelta(days=1)
    # Ensure we're using the correct date range
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
        if not scraper.setup_session():
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
            
            time.sleep(random.uniform(2, 4))  # Rate limiting
        
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
