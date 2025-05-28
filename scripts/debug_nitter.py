import requests
from bs4 import BeautifulSoup
import logging
from datetime import datetime, timedelta
import pytz

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def debug_multiple_nitter_instances():
    """Debug script to find working Nitter instances and examine date formats"""
    
    instances = [
        "https://nitter.poast.org",
        "https://nitter.privacydev.net", 
        "https://nitter.unixfox.eu",
        "https://nitter.kavin.rocks",
        "https://nitter.net",
        "https://nitter.rawbit.ninja",
        "https://nitter.1d4.us",
        "https://nitter.moomoo.me"
    ]
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
    })
    
    working_instance = None
    
    # First, find a working instance
    print("Testing Nitter instances...")
    for instance in instances:
        try:
            url = f"{instance}/openai"
            print(f"Testing: {url}")
            response = session.get(url, timeout=10)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                # Check if it looks like a real Nitter page
                if soup.find('div', class_='timeline') or soup.find('div', class_='profile') or soup.find('div', class_='timeline-item'):
                    print(f"SUCCESS: Found working instance: {instance}")
                    working_instance = instance
                    break
                else:
                    print(f"  Status 200 but doesn't look like Nitter")
            else:
                print(f"  Failed with status: {response.status_code}")
                
        except Exception as e:
            print(f"  Error: {e}")
    
    if not working_instance:
        print("No working Nitter instances found. Let me show you what a typical Nitter page structure should look like...")
        
        # Show expected Nitter HTML structure based on typical format
        print("""
TYPICAL NITTER HTML STRUCTURE:
==============================

<div class="timeline-item">
    <div class="tweet">
        <div class="tweet-header">
            <span class="tweet-date">
                <a href="/openai/status/xxx" title="May 27, 2025 · 3:45 PM UTC">3:45 PM · May 27, 2025</a>
            </span>
        </div>
        <div class="tweet-content">
            <div class="tweet-body">Tweet text content here...</div>
        </div>
    </div>
</div>

COMMON DATE FORMATS:
===================
- "May 27, 2025 · 3:45 PM UTC" (in title attribute)
- "3:45 PM · May 27, 2025" (displayed text)
- "May 27, 2025 · 15:45 UTC" (24-hour format)

DATE PARSING SHOULD HANDLE:
===========================
- %b %d, %Y · %I:%M %p UTC  (May 27, 2025 · 3:45 PM UTC)
- %b %d, %Y · %H:%M UTC     (May 27, 2025 · 15:45 UTC)
- %I:%M %p · %b %d, %Y      (3:45 PM · May 27, 2025)
- %H:%M · %b %d, %Y         (15:45 · May 27, 2025)
        """)
        return
    
    # Analyze the working instance
    print(f"\nAnalyzing working instance: {working_instance}")
    analyze_nitter_structure(session, working_instance)

def analyze_nitter_structure(session, instance):
    """Analyze the structure of a working Nitter instance"""
    
    url = f"{instance}/openai"
    print(f"\nFetching: {url}")
    
    try:
        response = session.get(url, timeout=30)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Check page title
        title = soup.title.string if soup.title else 'No title'
        print(f"Page title: {title}")
        
        # Find tweet containers
        selectors_to_try = [
            'div.timeline-item',
            'div.tweet',
            'article'
        ]
        
        tweet_containers = []
        for selector in selectors_to_try:
            containers = soup.select(selector)
            if containers:
                tweet_containers = containers
                print(f"Found {len(containers)} containers using: {selector}")
                break
        
        if not tweet_containers:
            print("No tweet containers found")
            return
        
        # Analyze first few tweets
        print(f"\nAnalyzing first 3 tweets:")
        for i, container in enumerate(tweet_containers[:3]):
            print(f"\n--- Tweet {i+1} ---")
            
            # Look for date elements
            date_elements = [
                container.find('span', class_='tweet-date'),
                container.find('time'),
                container.find('a', attrs={'title': True})
            ]
            
            date_found = False
            for date_elem in date_elements:
                if date_elem:
                    print(f"Date element: <{date_elem.name}> class={date_elem.get('class')}")
                    
                    if date_elem.get('title'):
                        print(f"  Title: '{date_elem.get('title')}'")
                    
                    if date_elem.get('datetime'):
                        print(f"  Datetime: '{date_elem.get('datetime')}'")
                    
                    text = date_elem.get_text(strip=True)
                    if text:
                        print(f"  Text: '{text}'")
                    
                    date_found = True
                    break
            
            if not date_found:
                print("  No date element found")
            
            # Look for content
            content_elem = (
                container.find('div', class_='tweet-content') or
                container.find('div', class_='tweet-body') or
                container.find('p')
            )
            
            if content_elem:
                content = content_elem.get_text(strip=True)
                print(f"  Content: '{content[:100]}...'")
            else:
                print("  No content found")
                
        # Show current date for reference
        utc = pytz.UTC
        now = datetime.now(utc)
        yesterday = now - timedelta(days=1)
        print(f"\nReference dates:")
        print(f"Current time: {now}")
        print(f"Yesterday: {yesterday}")
        print(f"Yesterday formatted: {yesterday.strftime('%b %d, %Y')}")
        
    except Exception as e:
        print(f"Error analyzing instance: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_multiple_nitter_instances()
