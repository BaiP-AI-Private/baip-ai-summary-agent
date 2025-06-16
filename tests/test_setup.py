#!/usr/bin/env python3
"""
Test script to verify the Twitter scraper setup
"""

import os
import sys
from dotenv import load_dotenv

def test_dependencies():
    """Test if all required dependencies are available"""
    print("Testing dependencies...")
    
    try:
        import playwright
        print("✓ Playwright installed")
    except ImportError:
        print("✗ Playwright not installed - run: pip install playwright")
        return False
    
    try:
        import jmespath
        print("✓ JMESPath installed")
    except ImportError:
        print("✗ JMESPath not installed - run: pip install jmespath")
        return False
    
    try:
        from playwright.async_api import async_playwright
        print("✓ Playwright async API available")
    except ImportError:
        print("✗ Playwright async API not available")
        return False
    
    return True

def test_environment():
    """Test if environment variables are configured"""
    print("\nTesting environment variables...")
    
    load_dotenv()
    load_dotenv(dotenv_path='../.env')  # Correct path from tests directory
    
    slack_url = os.getenv("SLACK_WEBHOOK_URL")
    openai_key = os.getenv("OPENAI_API_KEY")
    
    if slack_url:
        print("✓ SLACK_WEBHOOK_URL configured")
    else:
        print("✗ SLACK_WEBHOOK_URL not found in .env file")
        return False
    
    if openai_key:
        print("✓ OPENAI_API_KEY configured")
    else:
        print("✗ OPENAI_API_KEY not found in .env file")
        return False
    
    return True

async def test_playwright():
    """Test if Playwright can launch a browser"""
    print("\nTesting Playwright browser launch...")
    
    try:
        from playwright.async_api import async_playwright
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto("https://example.com")
            title = await page.title()
            await browser.close()
            
        print(f"✓ Browser test successful - got title: {title}")
        return True
        
    except Exception as e:
        print(f"✗ Browser test failed: {e}")
        print("Try running: playwright install chromium")
        return False

async def main():
    """Run all tests"""
    print("Twitter Scraper Setup Test\n" + "="*30)
    
    deps_ok = test_dependencies()
    env_ok = test_environment()
    
    if deps_ok:
        browser_ok = await test_playwright()
    else:
        browser_ok = False
    
    print("\n" + "="*30)
    if deps_ok and env_ok and browser_ok:
        print("✓ All tests passed! The scraper should work correctly.")
        print("\nRun the scraper with: python twitter_scraper_scrapfly.py")
    else:
        print("✗ Some tests failed. Please fix the issues above.")
        sys.exit(1)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
