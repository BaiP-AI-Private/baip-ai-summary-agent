# Scripts Directory

This directory contains all the scripts and utilities for the AI Summary Agent.

## Main Scripts

### `tweet_scraper.py`
The main tweet scraping and summarization script.
- Scrapes tweets from AI companies using Nitter instances
- Generates AI-powered summaries using OpenAI
- Posts daily summaries to Slack
- Includes fallback mechanisms for when services are unavailable

**Usage:**
```bash
cd scripts
python tweet_scraper.py
```

### `ai_summary_agent.py`
Alternative/backup implementation of the summary agent.

## Test Scripts

### `test_slack.py`
Tests the Slack webhook integration.
```bash
python test_slack.py
```

### `test_openai.py`
Tests the OpenAI API connectivity and quota.
```bash
python test_openai.py
```

### `test_full_functionality.py`
Comprehensive test of all tweet scraper functionality with mock data.
```bash
python test_full_functionality.py
```

## Environment Setup

All scripts expect the `.env` file to be in the parent directory (`../`).

Required environment variables:
- `OPENAI_API_KEY` - Your OpenAI API key
- `SLACK_WEBHOOK_URL` - Your Slack webhook URL

## Logs

Script logs are generated in:
- `tweet_scraper.log` - Main script logs
- `../tweet_scraper.log` - Root directory logs (for backward compatibility)
