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
        logging.FileHandler('../tweet_scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables - try multiple paths for flexibility
load_dotenv()  # Try current directory first
load_dotenv(dotenv_path='../.env')  # Try parent directory
load_dotenv(dotenv_path='.env')  # Try explicit current directory

# Debug environment variables
api_key = os.getenv("OPENAI_API_KEY")
slack_url = os.getenv("SLACK_WEBHOOK_URL")
logger.info(f"OpenAI API key present: {bool(api_key)}")
logger.info(f"Slack webhook URL present: {bool(slack_url)}")

# Initialize OpenAI client with error handling
client = None
try:
    if not api_key:
        logger.error("OPENAI_API_KEY environment variable not found")
        client = None
    else:
        # Try to initialize with explicit parameters to avoid proxy issues
        client = OpenAI(
            api_key=api_key,
            timeout=30.0,
            max_retries=2
        )
        logger.info("OpenAI client initialized successfully")
except TypeError as te:
    logger.warning(f"OpenAI client initialization failed (TypeError): {te}")
    # Try without optional parameters that might cause issues
    try:
        client = OpenAI(api_key=api_key)
        logger.info("OpenAI client initialized with minimal parameters")
    except Exception as e3:
        logger.error(f"Minimal OpenAI initialization also failed: {e3}")
        client = None
except Exception as e:
    logger.warning(f"Failed to initialize OpenAI client: {e}")
    # Try alternative initialization for older versions
    try:
        import openai
        openai.api_key = api_key
        client = None  # Will use legacy API calls
        logger.info("Using legacy OpenAI API initialization")
    except Exception as e2:
        logger.error(f"Failed to initialize OpenAI with legacy method: {e2}")
        client = None

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

# Multiple Nitter instances (updated list of more reliable instances)
NITTER_INSTANCES = [
    "https://nitter.net",
    "https://nitter.unixfox.eu",
    "https://nitter.kavin.rocks", 
    "https://nitter.poast.org",
    "https://nitter.privacydev.net",
    "https://nitter.rawbit.ninja",
    "https://nitter.moomoo.me",
    "https://nitter.fdn.fr",
    "https://nitter.nixnet.services",
    "https://nitter.42l.fr"
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
        """Find a working source (Nitter instances)"""
        logger.info("Searching for working Nitter instances...")
        logger.info(f"Will test {len(NITTER_INSTANCES)} instances with 20s timeout each")
        
        for i, instance in enumerate(NITTER_INSTANCES):
            logger.info(f"Testing instance {i+1}/{len(NITTER_INSTANCES)}: {instance}")
            
            if self._test_nitter_instance(instance):
                self.current_instance = instance
                self.current_source_type = "nitter"
                logger.info(f"SUCCESS: Successfully found working Nitter instance: {instance}")
                return
            else:
                logger.info(f"FAILED: Instance {instance} is not working")
        
        # If nothing works, we'll still try to proceed with fallback message
        logger.error("No working sources found after testing all instances - will use fallback message")
        self.current_instance = None
        self.current_source_type = None

    def _test_nitter_instance(self, instance):
        """Test if a Nitter instance is working with improved patience and validation"""
        try:
            if instance in self.instance_retry_delays:
                delay = self.instance_retry_delays[instance]
                if datetime.now() < delay:
                    logger.debug(f"Instance {instance} in cooldown until {delay}")
                    return False

            # Try multiple test approaches
            test_approaches = [
                f"{instance}/OpenAI",
                f"{instance}/elonmusk",  # Alternative popular account
                f"{instance}",           # Just the homepage
            ]
            
            for i, test_url in enumerate(test_approaches):
                logger.debug(f"Testing URL approach {i+1}: {test_url}")
                
                try:
                    # Increase timeout and be more patient
                    response = self.session.get(test_url, timeout=25, allow_redirects=True)
                    
                    logger.debug(f"Response status: {response.status_code}")
                    logger.debug(f"Final URL: {response.url}")
                    
                    # Check for obvious redirect patterns that indicate issues
                    suspicious_domains = ["status.d420.de", "blocked", "error", "maintenance", "coaufu.com", "redirect", "spam"]
                    if any(pattern in response.url.lower() for pattern in suspicious_domains):
                        logger.debug(f"Instance {instance} redirected to suspicious domain: {response.url}")
                        continue

                    if response.status_code == 200:
                        # Be less strict about content validation
                        content_lower = response.text.lower()
                        
                        # Check for basic Nitter indicators (more flexible)
                        nitter_indicators = [
                            'nitter',           # The word "nitter" appears
                            'twitter',          # Twitter-related content
                            'tweet',            # Tweet-related content  
                            'timeline',         # Timeline elements
                            'profile',          # Profile elements
                        ]
                        
                        # For homepage, look for different indicators
                        if test_url.endswith(instance):
                            nitter_indicators.extend(['privacy', 'alternative', 'frontend'])
                        else:
                            # For profile pages, look for account-specific content
                            account_name = test_url.split('/')[-1].lower()
                            nitter_indicators.extend([account_name, f'@{account_name}'])
                        
                        indicators_found = sum(1 for indicator in nitter_indicators if indicator in content_lower)
                        logger.debug(f"Found {indicators_found}/{len(nitter_indicators)} indicators")
                        
                        if indicators_found >= 2:  # More flexible - just need 2 indicators
                            logger.info(f"SUCCESS: Instance {instance} appears to be working (found {indicators_found} indicators via approach {i+1})")
                            return True
                        elif indicators_found >= 1 and len(response.text) > 1000:  # Has some content and reasonable size
                            logger.info(f"SUCCESS: Instance {instance} appears to be working (minimal validation passed)")
                            return True
                        else:
                            logger.debug(f"Approach {i+1} for {instance} doesn't look like Nitter (only {indicators_found} indicators)")
                            
                    elif response.status_code == 429:
                        cooldown = datetime.now() + timedelta(seconds=300)  # 5 min cooldown for rate limit
                        self.instance_retry_delays[instance] = cooldown
                        logger.warning(f"Instance {instance} rate limited, cooling down until {cooldown}")
                        break  # Don't try other approaches if rate limited
                    else:
                        logger.debug(f"Approach {i+1} for {instance} returned status {response.status_code}")
                        
                except Exception as approach_error:
                    logger.debug(f"Approach {i+1} for {instance} failed: {approach_error}")
                    continue
                
        except Exception as e:
            logger.debug(f"Instance {instance} test failed: {e}")
            
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

    def _parse_tweet_date(self, date_str):
        """Parse tweet date from various Nitter formats"""
        if not date_str:
            return None
            
        try:
            # Common Nitter date formats
            formats = [
                '%b %d, %Y · %I:%M %p UTC',     # May 27, 2025 · 3:45 PM UTC
                '%b %d, %Y · %H:%M UTC',        # May 27, 2025 · 15:45 UTC
                '%I:%M %p · %b %d, %Y',         # 3:45 PM · May 27, 2025
                '%H:%M · %b %d, %Y',            # 15:45 · May 27, 2025
                '%b %d, %Y at %I:%M %p UTC',    # May 27, 2025 at 3:45 PM UTC
                '%b %d, %Y at %H:%M UTC',       # May 27, 2025 at 15:45 UTC
                '%Y-%m-%d %H:%M:%S UTC',        # 2025-05-27 15:45:30 UTC
                '%b %d, %Y',                    # May 27, 2025 (just date)
            ]
            
            for fmt in formats:
                try:
                    tweet_date = datetime.strptime(date_str.strip(), fmt)
                    # If no timezone info in format, assume UTC
                    if tweet_date.tzinfo is None:
                        tweet_date = pytz.UTC.localize(tweet_date)
                    return tweet_date
                except ValueError:
                    continue
                    
            logger.debug(f"Could not parse date: '{date_str}'")
            return None
            
        except Exception as e:
            logger.error(f"Error parsing date '{date_str}': {e}")
            return None

    def get_user_tweets(self, username, start_date, end_date):
        """Get tweets from a user within date range"""
        if not self.current_instance:
            return []
            
        tweets = []
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                url = f"{self.current_instance}/{username}"
                logger.info(f"Fetching from URL: {url} (attempt {attempt + 1}/{max_retries})")

                response = self.session.get(url, timeout=30)
                
                if response.status_code == 200:
                    # Success - process the response
                    break
                elif response.status_code in [502, 503, 504]:
                    # Server errors - the instance might be overloaded
                    logger.warning(f"Server error {response.status_code} for {username} on attempt {attempt + 1}")
                    if attempt < max_retries - 1:
                        logger.info(f"Retrying in 5 seconds...")
                        time.sleep(5)
                        continue
                    else:
                        logger.error(f"Failed to fetch tweets for {username} after {max_retries} attempts: {response.status_code}")
                        return []
                elif response.status_code == 429:
                    # Rate limited - try a different instance if available
                    logger.warning(f"Rate limited for {username}, marking instance for cooldown")
                    cooldown = datetime.now() + timedelta(minutes=10)
                    self.instance_retry_delays[self.current_instance] = cooldown
                    # Try to find another instance
                    old_instance = self.current_instance
                    self._find_working_source()
                    if self.current_instance and self.current_instance != old_instance:
                        logger.info(f"Switched to new instance: {self.current_instance}")
                        continue
                    else:
                        logger.error(f"No alternative instances available")
                        return []
                else:
                    logger.error(f"Failed to fetch tweets for {username}: {response.status_code}")
                    return []
                    
            except Exception as e:
                logger.error(f"Error fetching tweets for {username} on attempt {attempt + 1}: {e}")
                if attempt < max_retries - 1:
                    time.sleep(3)
                    continue
                else:
                    return []

        try:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Debug: Show a snippet of the HTML structure
            logger.debug(f"Page title: {soup.title.string if soup.title else 'No title'}")
            logger.debug(f"HTML content length: {len(response.text)} characters")
            
            # Try multiple selectors for Nitter
            tweet_containers = []
            selectors = ['div.timeline-item', 'div.tweet', 'article', 'div[class*="tweet"]', 'div[class*="post"]']
                
            for selector in selectors:
                containers = soup.select(selector)
                logger.debug(f"Selector '{selector}' found {len(containers)} elements")
                if containers and not tweet_containers:
                    tweet_containers = containers[:10]  # Limit to first 10
                    logger.info(f"Using selector '{selector}' - found {len(containers)} tweet containers")
                    break
            
            if not tweet_containers:
                logger.warning(f"No tweets found for {username}")
                # Debug: Show some of the page structure
                main_content = soup.find('main') or soup.find('body')
                if main_content:
                    logger.debug("Available div classes in main content:")
                    divs = main_content.find_all('div', limit=10)
                    for div in divs:
                        classes = div.get('class', [])
                        if classes:
                            logger.debug(f"  div.{'.'.join(classes)}")
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

                    # Extract and parse tweet date
                    tweet_date = None
                    date_element = (
                        container.find('span', class_='tweet-date') or
                        container.find('time') or
                        container.find('a', attrs={'title': True})
                    )
                    
                    if date_element:
                        # Try to get date from title attribute first (most reliable)
                        date_str = date_element.get('title')
                        if not date_str:
                            # Fall back to datetime attribute
                            date_str = date_element.get('datetime')
                        if not date_str:
                            # Fall back to element text
                            date_str = date_element.get_text(strip=True)
                        
                        if date_str:
                            tweet_date = self._parse_tweet_date(date_str)
                            if tweet_date:
                                logger.debug(f"Parsed tweet date: {tweet_date} from '{date_str}'")

                    # Check if tweet is within our date range
                    include_tweet = False
                    if tweet_date:
                        if start_date <= tweet_date <= end_date:
                            include_tweet = True
                            logger.debug(f"Tweet from {tweet_date} is within range {start_date} to {end_date}")
                        else:
                            logger.debug(f"Tweet from {tweet_date} is outside range {start_date} to {end_date}")
                    else:
                        # If we can't parse the date, include it as a fallback (recent tweets)
                        # This helps when Nitter changes formats or has issues
                        include_tweet = True
                        logger.debug(f"No date found, including tweet as fallback: {tweet_text[:50]}...")
                    
                    if include_tweet:
                        tweets.append(f"@{username}: {tweet_text}")
                        logger.info(f"Added tweet from {username}: {tweet_text[:100]}...")
                        
                        # Limit tweets per account to avoid overwhelming the summary
                        if len(tweets) >= 8:  # Increased limit slightly
                            break

                except Exception as e:
                    logger.error(f"Error parsing tweet container: {e}")
                    continue

        except Exception as e:
            logger.error(f"Error processing response for {username}: {e}")

        logger.info(f"Found {len(tweets)} tweets for {username}")
        return tweets

    def generate_no_tweets_message(self):
        """Generate a simple message when no tweets are found"""
        if self.current_instance:
            return f"No tweets found from monitored AI companies in the last 24 hours. The monitoring system successfully connected to Nitter but the accounts may not have posted recently."
        else:
            return "No tweets found from monitored AI companies in the last 24 hours. Nitter services are currently experiencing connectivity issues."

    def generate_manual_summary(self, tweets):
        """Generate a manual summary when OpenAI is unavailable"""
        summary = "**Daily AI Summary - Manual Overview**\n\n"
        
        # Extract key topics from tweets
        topics = {
            "model": ["gpt", "claude", "gemini", "llama", "mistral", "model"],
            "api": ["api", "endpoint", "integration", "developer"],
            "research": ["research", "paper", "study", "breakthrough"],
            "product": ["launch", "release", "announce", "new", "update"],
            "partnership": ["partner", "collaboration", "team", "join"]
        }
        
        categorized = {}
        for tweet in tweets[:20]:
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
                    summary += f"• **{category.title()}**: {len(category_tweets)} significant updates detected\n"
            
            summary += f"\n**Activity Overview:**\n"
            summary += f"• Total significant posts analyzed: {len(tweets)}\n"
            summary += f"• Categories with activity: {len([c for c in categorized.values() if c])}\n"
            summary += f"• Time period: Last 5 business days\n"
        else:
            summary += "• Routine social media activity detected\n"
            summary += "• No major business developments identified\n"
            summary += f"• {len(tweets)} posts analyzed from monitored companies\n"
        
        summary += "\n*Note: Manual analysis performed due to AI service unavailability. For detailed insights, AI-powered analysis will resume when service is restored.*"
        return summary

    def generate_summary(self, tweets):
        """Generate summary using OpenAI with updated API and fallbacks"""
        if not tweets:
            return self.generate_no_tweets_message()

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
            # Try new OpenAI client first
            if client:
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.3,
                    max_tokens=600
                )
                return response.choices[0].message.content.strip()
            else:
                # Fall back to legacy OpenAI API
                import openai
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.3,
                    max_tokens=600
                )
                return response.choices[0].message.content.strip()
                
        except Exception as e:
            logger.error(f"Error generating summary: {e}")
            
            # Check if it's a quota error and provide a meaningful fallback
            if "insufficient_quota" in str(e) or "exceeded" in str(e).lower():
                logger.warning("OpenAI API quota exceeded, generating manual summary")
                return self.generate_manual_summary(tweets)
            else:
                logger.warning("OpenAI API error, generating manual summary")
                return self.generate_manual_summary(tweets)

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
            logger.info("Found working source, attempting to scrape tweets...")
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
            logger.warning("No working sources available, will use fallback message")
        
        logger.info(f"Successfully processed {successful_accounts}/{len(X_ACCOUNTS)} accounts")
        logger.info(f"Total tweets collected: {len(all_tweets)}")
        
        # Generate summary
        if all_tweets:
            summary = scraper.generate_summary(all_tweets)
            message = f"{summary}\n\n_Processed {successful_accounts}/{len(X_ACCOUNTS)} accounts • {len(all_tweets)} total tweets_"
            logger.info("Generated summary from scraped tweets")
        else:
            summary = scraper.generate_no_tweets_message()
            message = summary  # Just the simple message, no additional metadata
            logger.info("No tweets found from any monitored accounts")
        
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
            error_message = f"*Error Alert*: The AI summary agent encountered a critical error:\n```{str(e)}```\nPlease check the logs for more details."
            error_scraper.send_to_slack(error_message)
        except Exception as slack_error:
            logger.error(f"Failed to send error notification to Slack: {slack_error}")

if __name__ == "__main__":
    main()
