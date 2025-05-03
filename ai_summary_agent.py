import os
import json
import openai
import tweepy
import certifi
from datetime import datetime, timedelta
from dotenv import load_dotenv
import requests

# Load environment variables from .env
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

# === CONFIG ===
AI_ACCOUNTS = [
    "OpenAI",
    "xai",
    "AnthropicAI",
    "GoogleDeepMind",
    "MistralAI"
]

TWEET_LIMIT = 100  # Max tweets to fetch per account

# === UTILITIES ===

def validate_env():
    required_vars = ["OPENAI_API_KEY", "SLACK_WEBHOOK_URL", 
                     "TWITTER_API_KEY", "TWITTER_API_SECRET", 
                     "TWITTER_ACCESS_TOKEN", "TWITTER_ACCESS_SECRET",
                     "TWITTER_BEARER_TOKEN"]
    
    missing = [var for var in required_vars if not os.getenv(var)]
    if missing:
        raise EnvironmentError(f"Missing environment variables: {', '.join(missing)}")

def get_yesterday_date_range():
    yesterday = datetime.utcnow() - timedelta(days=1)
    start = yesterday.replace(hour=0, minute=0, second=0)
    end = yesterday.replace(hour=23, minute=59, second=59)
    # Format for Twitter API v2
    return start.strftime("%Y-%m-%dT00:00:00Z"), end.strftime("%Y-%m-%dT23:59:59Z")

def setup_twitter_client():
    """Create Twitter API v2 client"""
    client = tweepy.Client(
        bearer_token=os.getenv("TWITTER_BEARER_TOKEN"),
        consumer_key=os.getenv("TWITTER_API_KEY"),
        consumer_secret=os.getenv("TWITTER_API_SECRET"),
        access_token=os.getenv("TWITTER_ACCESS_TOKEN"),
        access_token_secret=os.getenv("TWITTER_ACCESS_SECRET")
    )
    return client

def fetch_tweets(client, account, start_time, end_time):
    """Fetch tweets using Twitter API v2"""
    print(f"Fetching tweets for {account} from {start_time} to {end_time}")
    
    try:
        # First, get the user ID
        user = client.get_user(username=account)
        if not user.data:
            print(f"Could not find user: {account}")
            return []
        
        user_id = user.data.id
        
        # Then get the user's tweets within the time range
        tweets = client.get_users_tweets(
            id=user_id,
            start_time=start_time,
            end_time=end_time,
            max_results=TWEET_LIMIT,
            tweet_fields=['created_at', 'text'],
            exclude=['retweets', 'replies']
        )
        
        if not tweets.data:
            print(f"No tweets found for {account} in the specified time range")
            return []
        
        return [tweet.text for tweet in tweets.data]
    
    except tweepy.TweepyException as e:
        print(f"Error fetching tweets for {account}: {str(e)}")
        return []

def summarize_with_gpt(tweet_texts):
    if not tweet_texts:
        return "No tweets to summarize for this period."

    joined_text = "\n\n".join(tweet_texts)

    # Limit length to prevent API errors
    if len(joined_text) > 10000:
        joined_text = joined_text[:10000] + "\n\n[Truncated due to length]"

    prompt = f"""
You are an AI assistant. Summarize the main announcements, product updates, or insights from the following tweets by AI companies.

Tweets:
{joined_text}

Summary:
"""
    response = openai.ChatCompletion.create(
        model="gpt-4-turbo",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=500
    )
    return response.choices[0].message.content.strip()

def post_to_slack(summary_text):
    webhook_url = os.getenv("SLACK_WEBHOOK_URL")
    payload = {
        "text": f"🧠 *Daily AI Summary*:\n\n{summary_text}"
    }

    # Use certifi for SSL certificate verification
    response = requests.post(webhook_url, json=payload, verify=certifi.where())
    if response.status_code == 200:
        print("✅ Summary posted to Slack successfully.")
    else:
        print(f"❌ Failed to post to Slack: {response.status_code}, {response.text}")

# === MAIN ===

def main():
    validate_env()
    
    # Set global SSL certificate environment variables
    os.environ["REQUESTS_CA_BUNDLE"] = certifi.where()
    os.environ["SSL_CERT_FILE"] = certifi.where()
    
    # Print certificate path for debugging
    print(f"Using certificate path: {certifi.where()}")
    
    start_time, end_time = get_yesterday_date_range()
    print(f"Fetching tweets from {start_time} to {end_time}")
    
    # Initialize Twitter API client
    twitter_client = setup_twitter_client()
    
    all_tweets = []
    for account in AI_ACCOUNTS:
        tweets = fetch_tweets(twitter_client, account, start_time, end_time)
        if tweets:
            print(f"Found {len(tweets)} tweets for {account}")
            all_tweets.extend(tweets)
        else:
            print(f"No tweets found for {account}")

    if not all_tweets:
        summary = "No tweets found from the monitored AI accounts in the last 24 hours."
    else:
        print(f"\n🔍 Generating daily AI summary from {len(all_tweets)} tweets...\n")
        summary = summarize_with_gpt(all_tweets)
    
    print(summary)
    post_to_slack(summary)

if __name__ == "__main__":
    main()
