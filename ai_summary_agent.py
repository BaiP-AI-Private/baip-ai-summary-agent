import os
import json
import openai
import requests
import certifi
from datetime import datetime, timedelta
from dotenv import load_dotenv
import time
import random
import re

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

TWEET_LIMIT = 10
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.81 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.81 Safari/537.36"
]

# === UTILITIES ===

def validate_env():
    required_vars = ["OPENAI_API_KEY", "SLACK_WEBHOOK_URL", "TWITTER_USERNAME", "TWITTER_PASSWORD"]
    missing = [var for var in required_vars if not os.getenv(var)]
    if missing:
        raise EnvironmentError(f"Missing environment variables: {', '.join(missing)}")

def get_yesterday_date_range():
    yesterday = datetime.utcnow() - timedelta(days=1)
    start = yesterday.replace(hour=0, minute=0, second=0)
    end = yesterday.replace(hour=23, minute=59, second=59)
    return start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d")

def get_twitter_auth_token():
    """Get authentication tokens using Twitter's guest flow"""
    session = requests.Session()
    session.headers.update({
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.5",
        "Connection": "keep-alive",
    })

    # Get guest token
    try:
        guest_response = session.post(
            "https://api.twitter.com/1.1/guest/activate.json",
            verify=certifi.where()
        )
        if guest_response.status_code == 200:
            guest_token = guest_response.json().get("guest_token")
            return {
                "guest_token": guest_token,
                "session": session
            }
    except Exception as e:
        print(f"Error getting guest token: {e}")
    
    return None

def fetch_user_id(username, auth_data):
    """Fetch user ID using GraphQL API"""
    url = f"https://api.twitter.com/graphql/4S2ihIKfF3xhp-ENxvUAfQ/UserByScreenName?variables=%7B%22screen_name%22%3A%22{username}%22%2C%22withHighlightedLabel%22%3Atrue%7D"
    
    headers = {
        "User-Agent": random.choice(USER_AGENTS),
        "Authorization": "Bearer AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs%3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA",
        "x-guest-token": auth_data.get("guest_token"),
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.5",
    }
    
    try:
        response = auth_data["session"].get(url, headers=headers, verify=certifi.where())
        if response.status_code == 200:
            data = response.json()
            return data["data"]["user"]["rest_id"]
    except Exception as e:
        print(f"Error getting user ID for {username}: {e}")
    
    return None

def fetch_user_tweets(user_id, auth_data, start_date, end_date):
    """Fetch tweets using Twitter's GraphQL API"""
    url = "https://api.twitter.com/graphql/zICd6x_warY0bzMRm-piIg/UserTweets"
    
    headers = {
        "User-Agent": random.choice(USER_AGENTS),
        "Authorization": "Bearer AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs%3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA",
        "x-guest-token": auth_data.get("guest_token"),
        "Content-Type": "application/json",
        "Accept": "*/*",
    }
    
    variables = {
        "userId": user_id,
        "count": TWEET_LIMIT,
        "includePromotedContent": False,
        "withVoice": True,
        "withV2Timeline": True,
    }
    
    features = {
        "responsive_web_graphql_timeline_navigation_enabled": True,
        "responsive_web_graphql_skip_user_profile_image_extensions_enabled": False,
        "responsive_web_graphql_exclude_directive_enabled": True,
    }
    
    params = {
        "variables": json.dumps(variables),
        "features": json.dumps(features),
    }
    
    try:
        response = auth_data["session"].get(url, headers=headers, params=params, verify=certifi.where())
        if response.status_code == 200:
            data = response.json()
            tweets = []
            
            instructions = data.get("data", {}).get("user", {}).get("result", {}).get("timeline_v2", {}).get("timeline", {}).get("instructions", [])
            
            for instruction in instructions:
                if instruction.get("type") == "TimelineAddEntries":
                    for entry in instruction.get("entries", []):
                        if "tweet" in entry.get("content", {}).get("itemContent", {}).get("tweet_results", {}).get("result", {}):
                            tweet = entry["content"]["itemContent"]["tweet_results"]["result"]["tweet"]
                            tweet_date = datetime.strptime(tweet["created_at"], "%a %b %d %H:%M:%S %z %Y").strftime("%Y-%m-%d")
                            if start_date <= tweet_date <= end_date:
                                tweets.append(tweet["full_text"])
            return tweets
    except Exception as e:
        print(f"Error fetching tweets: {e}")
    
    return []

def scrape_tweets_for_account(account, auth_data, start_date, end_date):
    """Scrape tweets for a specific account"""
    print(f"Scraping tweets for {account}")
    
    user_id = fetch_user_id(account, auth_data)
    if not user_id:
        print(f"Could not find user ID for {account}")
        return []
    
    tweets = fetch_user_tweets(user_id, auth_data, start_date, end_date)
    print(f"Found {len(tweets)} tweets for {account}")
    
    time.sleep(random.uniform(2, 5))
    return tweets

def summarize_with_gpt(tweet_texts):
    if not tweet_texts:
        return "No tweets to summarize for this period."

    joined_text = "\n\n".join(tweet_texts)
    if len(joined_text) > 10000:
        joined_text = joined_text[:10000] + "\n\n[Truncated due to length]"

    prompt = f"""Summarize the main announcements from these AI company tweets:
{joined_text}

Summary:"""
    
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

    try:
        response = requests.post(webhook_url, json=payload, verify=certifi.where())
        if response.status_code != 200:
            print(f"Failed to post to Slack: {response.status_code}")
    except Exception as e:
        print(f"Error posting to Slack: {e}")

def main():
    validate_env()
    os.environ["REQUESTS_CA_BUNDLE"] = certifi.where()
    
    print("Authenticating with Twitter...")
    auth_data = get_twitter_auth_token()
    if not auth_data:
        print("Using guest mode only - some features may be limited")
        return

    start_date, end_date = get_yesterday_date_range()
    print(f"Fetching tweets from {start_date} to {end_date}")
    
    all_tweets = []
    for account in AI_ACCOUNTS:
        tweets = scrape_tweets_for_account(account, auth_data, start_date, end_date)
        all_tweets.extend(tweets)
        time.sleep(random.uniform(1, 3))

    if not all_tweets:
        summary = "No tweets found from the monitored AI accounts in the last 24 hours."
    else:
        print(f"\nGenerating summary from {len(all_tweets)} tweets...")
        summary = summarize_with_gpt(all_tweets)
    
    print(summary)
    post_to_slack(summary)

if __name__ == "__main__":
    main()
