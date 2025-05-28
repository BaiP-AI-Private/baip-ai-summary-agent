# Twitter Scraper - New Implementation

## Overview
This is a modern Twitter/X.com scraper using the Playwright method recommended by Scrapfly. It captures background requests to reliably extract tweet data.

## Files Created
- `twitter_scraper_new.py` - Main scraper using Playwright
- `setup.sh` - Installation script
- Updated `requirements.txt` - Added new dependencies

## Setup Instructions

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Install Playwright browsers:**
   ```bash
   playwright install chromium
   ```

3. **Ensure .env file is configured:**
   ```
   SLACK_WEBHOOK_URL=your_webhook_url
   OPENAI_API_KEY=your_openai_key
   ```

## Running the Scraper

```bash
cd scripts
python twitter_scraper_new.py
```

## How It Works

1. **Playwright Browser**: Launches a headless Chromium browser
2. **Background Request Capture**: Intercepts XHR requests that load tweet data
3. **JSON Parsing**: Uses JMESPath to extract relevant data from Twitter's API responses
4. **Date Filtering**: Filters tweets to those from the previous 24 hours
5. **AI Summary**: Uses OpenAI to generate a summary of collected tweets
6. **Slack Notification**: Posts the summary to your configured Slack channel

## Advantages Over Old Script

- **More Reliable**: Uses Twitter's actual API endpoints instead of unreliable Nitter instances
- **Better Data Quality**: Gets structured JSON data with engagement metrics
- **Modern Architecture**: Async/await with proper error handling
- **Fallback Support**: Graceful degradation when services are unavailable

## Monitored Accounts
- OpenAI
- xAI
- AnthropicAI
- GoogleDeepMind
- MistralAI
- AIatMeta
- Cohere
- perplexity_ai
- scale_ai
- runwayml
- dair_ai

## Troubleshooting

**If Playwright fails to install:**
- Try: `pip install playwright==1.40.0`
- Then: `playwright install chromium`

**If scraping fails:**
- Check if X.com has updated their anti-bot measures
- The script includes error handling and will send a Slack notification if it fails

**Performance:**
- The script includes rate limiting (2-second delays between accounts)
- Uses headless browser for efficiency
- Filters to relevant tweets only
