import os
import subprocess
import json
import openai
from datetime import datetime, timedelta
from dotenv import load_dotenv
import requests

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

def get_yesterday_date_range():
    yesterday = datetime.utcnow() - timedelta(days=1)
    start = yesterday.replace(hour=0, minute=0, second=0)
    end = yesterday.replace(hour=23, minute=59, second=59)
    return start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d")

def scrape_tweets(account, start_date, end_date):
    query = f"from:{account} since:{start_date} until:{end_date}"
    print(f"Scraping: {query}")
    result = subprocess.run(
        ["snscrape", "--jsonl", "--max-results", str(TWEET_LIMIT), "twitter-search", query],
        capture_output=True,
        text=True
    )
    tweets = [json.loads(line) for line in result.stdout.splitlines()]
    return [tweet["content"] for tweet in tweets]

def summarize_with_gpt(tweet_texts):
    if not tweet_texts:
        return "No tweets to summarize for this period."
    
    joined_text = "\n\n".join(tweet_texts)
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
    if not webhook_url:
        print("Slack webhook URL not found in environment.")
        return
    
    payload = {
        "text": f"🧠 *Daily AI Summary*:\n\n{summary_text}"
    }

    response = requests.post(webhook_url, json=payload)
    if response.status_code == 200:
        print("✅ Summary posted to Slack successfully.")
    else:
        print(f"❌ Failed to post to Slack: {response.text}")

def main():
    start_date, end_date = get_yesterday_date_range()
    all_tweets = []

    for account in AI_ACCOUNTS:
        tweets = scrape_tweets(account, start_date, end_date)
        all_tweets.extend(tweets)

    print("\n🔍 Generating daily AI summary...\n")
    summary = summarize_with_gpt(all_tweets)
    print(summary)
    post_to_slack(summary)

if __name__ == "__main__":
    main()
