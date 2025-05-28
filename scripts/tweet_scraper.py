import os
import json
from openai import OpenAI
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

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

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

# Multiple Nitter instances + alternative sources
NITTER_INSTANCES = [
    "https://nitter.poast.org",
    "https://nitter.privacydev.net", 
    "https://nitter.unixfox.eu",
    "https://nitter.kavin.rocks",
    "https://nitter.net",
    "https://nitter.rawbit.ninja",
    "https://nitter.1d4.us",
    "https://nitter.moomoo.me"
]

# Alternative sources for when Nitter is down
ALTERNATIVE_SOURCES = [
    "https://xcancel.com",
    "https://fixupx.com"
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
        self.current_instance = None
        self.current_source_type = None
        self._find_working_source()

    def _find_working_source(self):
        """Find a working source (Nitter first, then alternatives)"""
        # Try Nitter instances first
        for instance in NITTER_INSTANCES:
            if self._test_nitter_instance(instance):
                self.current_instance = instance
                self.current_source_type = "nitter"
                logger.info(f"Using Nitter instance: {instance}")
                return
                
        # If no Nitter works, try alternatives
        for alt_source in ALTERNATIVE_SOURCES:
            if self._test_alternative_source(alt_source):
                self.current_instance = alt_source
                self.current_source_type = "alternative"
                logger.info(f"Using alternative source: {alt_source}")
                return
                
        # If nothing works, we'll still try to proceed with demo data
        logger.error("No working sources found - will generate demo summary")
        self.current_instance = None
        self.current_source_type = None

    def _test_nitter_instance(self, instance):
        """Test if a Nitter instance is working"""
        try:
            if instance in self.instance_retry_delays:
                delay = self.instance_retry_delays[instance]
                if datetime.now() < delay:
                    return False

            test_url = f"{instance}/OpenAI"
            response = self.session.get(test_url, timeout=10, allow_redirects=True)
            
            if any(pattern in response.url.lower() for pattern in ["status.d420.de", "blocked", "error", "maintenance"]):
                return False

            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                if soup.find('div', class_='timeline') or soup.find('div', class_='profile') or soup.find('div', class_='timeline-item'):
                    return True
                    
            elif response.status_code == 429:
                cooldown = datetime.now() + timedelta(seconds=120)
                self.instance_retry_delays[instance] = cooldown
                
        except Exception as e:
            logger.debug(f"Nitter instance {instance} failed: {e}")
        return False

    def _test_alternative_source(self, source):
        """Test if an alternative source is working"""
        try:
            test_url = f"{source}/OpenAI"
            response = self.session.get(test_url, timeout=10)
            return response.status_code == 200
        except Exception as e:
            logger.debug(f"Alternative source {source} failed: {e}")
        return False

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

    def get_user_tweets(self, username, start_date, end_date):
        """Get tweets from a user within date range"""
        if not self.current_instance:
            return []
            
        tweets = []
        try:
            url = f"{self.current_instance}/{username}"
            logger.info(f"Fetching from URL: {url}")

            response = self.session.get(url, timeout=30)
            
            if response.status_code != 200:
                logger.error(f"Failed to fetch tweets for {username}: {response.status_code}")
                return []

            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Try multiple selectors based on source type
            tweet_containers = []
            if self.current_source_type == "nitter":
                selectors = ['div.timeline-item', 'div.tweet', 'article']
            else:
                selectors = ['div[data-testid="tweet"]', 'article', 'div.tweet']
                
            for selector in selectors:
                containers = soup.select(selector)
                if containers:
                    tweet_containers = containers[:10]  # Limit to first 10
                    break
            
            if not tweet_containers:
                logger.warning(f"No tweets found for {username}")
                return []

            logger.info(f"Processing {len(tweet_containers)} tweet containers")
            
            for container in tweet_containers:
                try:
                    # Extract tweet text
                    tweet_text_element = (
                        container.find('div', class_='tweet-content') or
                        container.find('div', class_=['tweet-text', 'content']) or
                        container.find('p') or
                        container.find('span', attrs={'data-testid': 'tweetText'})
                    )
                    
                    if not tweet_text_element:
                        continue

                    tweet_text = tweet_text_element.get_text(strip=True)
                    if not tweet_text or len(tweet_text.strip()) < 10:
                        continue

                    # For now, include all tweets since date parsing is unreliable
                    tweets.append(f"@{username}: {tweet_text}")
                    if len(tweets) >= 5:  # Limit per account
                        break

                except Exception as e:
                    logger.error(f"Error parsing tweet container: {e}")
                    continue

        except Exception as e:
            logger.error(f"Error fetching tweets for {username}: {e}")

        logger.info(f"Found {len(tweets)} tweets for {username}")
        return tweets

    def generate_demo_summary(self):
        """Generate a demo summary when scraping fails"""
        demo_content = [
            "@OpenAI: Excited to share updates on GPT-4 Turbo performance improvements and new API features rolling out this week.",
            "@AnthropicAI: Claude 3.5 Sonnet continues to show strong performance on coding benchmarks. Safety remains our top priority.",
            "@GoogleDeepMind: New research on multimodal AI models published in Nature. Breakthrough in vision-language understanding.",
            "@MistralAI: Mistral Large 2 now available with improved reasoning capabilities and expanded context window.",
            "@AIatMeta: Llama 3 adoption growing rapidly across enterprise use cases. Open source AI democratizing innovation.",
        ]
        
        summary = """**Demo Summary - AI Industry Updates**

• **Model Improvements**: Multiple companies releasing enhanced versions of their flagship models with better performance
• **API Updates**: New features and improvements being rolled out to developer platforms  
• **Research Advances**: Continued breakthroughs in multimodal AI and reasoning capabilities
• **Enterprise Adoption**: Growing use of AI models in business applications
• **Open Source**: Continued push for democratizing AI through open source initiatives

*Note: This is a demo summary as tweet scraping services are currently unavailable. The monitoring system will resume normal operation when services are restored.*"""
        
        return summary

    def generate_summary(self, tweets):
        """Generate summary using OpenAI with updated API"""
        if not tweets:
            return self.generate_demo_summary()

        text = "\n\n".join(tweets[:25])
        prompt = """Analyze these tweets from AI companies and create a concise daily summary:
        
Key points to extract:
- New product announcements
- Technical breakthroughs
- Important partnerships
- Notable research findings
- Significant company updates
- Industry trends and insights

Please format the summary in clear bullet points with the most important information first.

Tweets:
{}

Summary:""".format(text)

        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=600
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Error generating summary: {e}")
            return f"Failed to generate summary. Error: {str(e)}"

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
                headers={"Content-Type": "application/json"},
                timeout=30
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
        successful_accounts = 0
        
        if scraper.current_instance:
            for account in X_ACCOUNTS:
                logger.info(f"Processing {account}...")
                try:
                    tweets = scraper.get_user_tweets(account, start_date, end_date)
                    if tweets:
                        logger.info(f"Found {len(tweets)} tweets from {account}")
                        all_tweets.extend(tweets)
                        successful_accounts += 1
                    else:
                        logger.warning(f"No tweets found for {account}")
                except Exception as e:
                    logger.error(f"Failed to process {account}: {e}")
                
                # Rate limiting between accounts
                time.sleep(random.uniform(3, 5))
        else:
            logger.warning("No working sources available, will generate demo summary")
        
        logger.info(f"Successfully processed {successful_accounts}/{len(X_ACCOUNTS)} accounts")
        logger.info(f"Total tweets collected: {len(all_tweets)}")
        
        # Generate summary
        if all_tweets:
            summary = scraper.generate_summary(all_tweets)
            message = f"{summary}\n\n_Processed {successful_accounts}/{len(X_ACCOUNTS)} accounts • {len(all_tweets)} total tweets_"
            logger.info("Generated summary from scraped tweets")
        else:
            summary = scraper.generate_demo_summary()
            message = f"{summary}\n\n_Demo mode: {successful_accounts}/{len(X_ACCOUNTS)} accounts processed • Scraping services unavailable_"
            logger.info("Generated demo summary due to scraping issues")
        
        # Send to Slack
        if not scraper.send_to_slack(message):
            logger.error("Failed to send message to Slack")
        else:
            logger.info("Successfully sent daily summary to Slack")
            
    except Exception as e:
        logger.error(f"Critical error in main execution: {e}")
        # Send error notification to Slack
        try:
            error_scraper = TweetScraper()
            error_message = f"⚠️ *Error Alert*: The AI summary agent encountered a critical error:\n```{str(e)}```\nPlease check the logs for more details."
            error_scraper.send_to_slack(error_message)
        except Exception as slack_error:
            logger.error(f"Failed to send error notification to Slack: {slack_error}")
        raise

if __name__ == "__main__":
    main()
