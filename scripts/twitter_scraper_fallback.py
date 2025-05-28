"""
Fallback Twitter scraper using alternative methods
For when Playwright is not available or fails
"""

import os
import logging
import requests
from datetime import datetime
from openai import OpenAI
from dotenv import load_dotenv

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

# Load environment variables
load_dotenv()
load_dotenv(dotenv_path='../.env')

# Initialize OpenAI client
api_key = os.getenv("OPENAI_API_KEY")
client = None
if api_key:
    try:
        client = OpenAI(api_key=api_key)
    except Exception as e:
        logger.error(f"Failed to initialize OpenAI client: {e}")

# Configuration  
X_ACCOUNTS = ["OpenAI", "xai", "AnthropicAI", "GoogleDeepMind", "MistralAI",
              "AIatMeta", "Cohere", "perplexity_ai", "scale_ai", "runwayml", "dair_ai"]


class TwitterScraperFallback:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'DNT': '1',
            'Connection': 'keep-alive',
        })