#!/bin/bash

# Setup script for the new Twitter scraper

echo "Setting up Twitter scraper dependencies..."

# Install Python dependencies
pip install playwright jmespath

# Install Playwright browsers
playwright install chromium

echo "Setup complete!"
echo ""
echo "To run the new scraper:"
echo "python twitter_scraper_new.py"
echo ""
echo "Make sure your .env file contains:"
echo "SLACK_WEBHOOK_URL=your_webhook_url"
echo "OPENAI_API_KEY=your_openai_key"
