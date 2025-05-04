import os
import json
import openai
import requests
import certifi
from datetime import datetime, timedelta
from dotenv import load_dotenv
import time
import random

# Load environment variables
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

# Configuration
AI_ACCOUNTS = [
    "OpenAI",
    "xai",
    "AnthropicAI",
    "GoogleDeepMind",
    "MistralAI"
]

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
]

def validate_env():
    required_vars = ["OPENAI_API_KEY", "SLACK_WEBHOOK_URL"]
    missing = [var for var in required_vars if not os.getenv(var)]
    if missing:
        raise EnvironmentError(f"Missing environment variables: {', '.join(missing)}")

def get_yesterday_date_range():
    yesterday = datetime.utcnow() - timedelta(days=1)
    start = yesterday.replace(hour=0, minute=0, second=0)
    end = yesterday.replace(hour=23, minute=59, second=59)
    return start, end

def get_twitter_session():
    """Create authenticated Twitter session with guest token"""
    session = requests.Session()
    session.headers.update({
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.9",
        "Origin": "https://twitter.com",
        "Referer": "https://twitter.com/",
    })

    # Get guest token
    try:
        response = session.post(
            "https://api.twitter.com/1.1/guest/activate.json",
            headers={"Authorization": "Bearer AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs%3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA"},
            verify=certifi.where()
        )
        if response.status_code == 200:
            guest_token = response.json().get("guest_token")
            session.headers.update({
                "x-guest-token": guest_token,
                "Authorization": "Bearer AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs%3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA"
            })
            return session
    except Exception as e:
        print(f"Error getting guest token: {e}")
    return None

def get_user_id(session, username):
    """Get user ID from screen name"""
    params = {
        "variables": json.dumps({"screen_name": username, "withHighlightedLabel": True})
    }
    try:
        response = session.get(
            "https://twitter.com/i/api/graphql/4S2ihIKfF3xhp-ENxvUAfQ/UserByScreenName",
            params=params,
            verify=certifi.where()
        )
        if response.status_code == 200:
            data = response.json()
            return data.get("data", {}).get("user", {}).get("rest_id")
    except Exception as e:
        print(f"Error getting user ID for {username}: {e}")
    return None

def get_user_tweets(session, user_id, start_date, end_date, limit=10):
    """Fetch user tweets within date range"""
    variables = {
        "userId": user_id,
        "count": limit,
        "includePromotedContent": False,
        "withQuickPromoteEligibilityTweetFields": False,
        "withVoice": True,
        "withV2Timeline": True
    }
    
    features = {
        "responsive_web_graphql_timeline_navigation_enabled": True,
        "responsive_web_graphql_skip_user_profile_image_extensions_enabled": False,
        "responsive_web_graphql_exclude_directive_enabled": True
    }
    
    params = {
        "variables": json.dumps(variables),
        "features": json.dumps(features)
    }
    
    try:
        response = session.get(
            "https://twitter.com/i/api/graphql/zICd6x_warY0bzMRm-piIg/UserTweets",
            params=params,
            verify=certifi.where()
        )
        
        if response.status_code == 200:
            tweets = []
            data = response.json()
            instructions = data.get("data", {}).get("user", {}).get("result", {}).get("timeline_v2", {}).get("timeline", {}).get("instructions", [])
            
            for instruction in instructions:
                if instruction.get("type") == "TimelineAddEntries":
                    for entry in instruction.get("entries", []):
                        content = entry.get("content", {})
                        if "itemContent" in content and "tweet_results" in content["itemContent"]:
                            tweet = content["itemContent"]["tweet_results"].get("result", {})
                            if "legacy" in tweet:
                                tweet_date = datetime.strptime(tweet["legacy"]["created_at"], "%a %b %d %H:%M:%S %z %Y")
                                if start_date <= tweet_date <= end_date:
                                    tweets.append(tweet["legacy"]["full_text"])
            return tweets
    except Exception as e:
        print(f"Error fetching tweets: {e}")
    return []

def summarize_tweets(tweets):
    if not tweets:
        return "No tweets found from monitored accounts in the last 24 hours."
    
    text = "\n\n".join(tweets[:20])  # Limit to first 20 tweets
    prompt = f"""Summarize the key points from these AI company tweets:
    
{text}

Summary should highlight important announcements, product updates, and insights in bullet points:"""
    
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500,
            temperature=0.3
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error generating summary: {e}")
        return "Failed to generate summary"

def post_to_slack(message):
    webhook_url = os.getenv("SLACK_WEBHOOK_URL")
    payload = {
        "text": f"🧠 *Daily AI Summary* 🧠\n\n{message}",
        "mrkdwn": True
    }
    
    try:
        response = requests.post(
            webhook_url,
            json=payload,
            headers={"Content-Type": "application/json"},
            verify=certifi.where()
        )
        if response.status_code != 200:
            print(f"Slack API error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Error posting to Slack: {e}")

def main():
    validate_env()
    os.environ["REQUESTS_CA_BUNDLE"] = certifi.where()
    
    print("Initializing Twitter session...")
    session = get_twitter_session()
    if not session:
        print("Failed to initialize Twitter session")
        post_to_slack("⚠️ Failed to initialize Twitter session for daily summary")
        return
    
    start_date, end_date = get_yesterday_date_range()
    print(f"Fetching tweets from {start_date.date()} to {end_date.date()}")
    
    all_tweets = []
    for account in AI_ACCOUNTS:
        print(f"Processing {account}...")
        user_id = get_user_id(session, account)
        if not user_id:
            print(f"Could not find user ID for {account}")
            continue
        
        tweets = get_user_tweets(session, user_id, start_date, end_date)
        if tweets:
            print(f"Found {len(tweets)} tweets from {account}")
            all_tweets.extend(tweets)
        
        time.sleep(random.uniform(1, 3))  # Rate limiting
    
    summary = summarize_tweets(all_tweets)
    print("\nGenerated Summary:\n")
    print(summary)
    
    post_to_slack(summary)
    print("Summary posted to Slack")

if __name__ == "__main__":
    main()
