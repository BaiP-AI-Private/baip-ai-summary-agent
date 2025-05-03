import os
import tweepy
import openai
import requests

# Load environment variables
openai.api_key = os.getenv("OPENAI_API_KEY")
bearer_token = os.getenv("TWITTER_BEARER_TOKEN")
slack_webhook_url = os.getenv("SLACK_WEBHOOK_URL")

# Step 1: Fetch Tweets using Twitter API v2 via Tweepy
client = tweepy.Client(bearer_token=bearer_token)

query = "openai -is:retweet lang:en"
response = client.search_recent_tweets(query=query, max_results=10)

if not response.data:
    print("No tweets found.")
    exit()

# Extract tweet texts
tweet_texts = [tweet.text for tweet in response.data]

# Step 2: Generate a summary using OpenAI
combined_text = "\n\n".join(tweet_texts)

prompt = (
    "Summarize the following tweets about OpenAI into a short daily summary:\n\n"
    f"{combined_text}"
)

print("Sending to OpenAI...")
response = openai.ChatCompletion.create(
    model="gpt-4",
    messages=[
        {"role": "system", "content": "You are a helpful assistant that summarizes trending tweets."},
        {"role": "user", "content": prompt},
    ],
    temperature=0.7,
)

summary = response.choices[0].message.content.strip()
print("\n--- Summary ---\n", summary)

# Step 3 (Optional): Send summary to Slack
if slack_webhook_url:
    slack_data = {
        "text": f"*Daily OpenAI Twitter Summary:*\n\n{summary}"
    }
    slack_response = requests.post(slack_webhook_url, json=slack_data)
    if slack_response.status_code != 200:
        print(f"Slack error: {slack_response.status_code} - {slack_response.text}")
    else:
        print("Summary posted to Slack successfully.")
