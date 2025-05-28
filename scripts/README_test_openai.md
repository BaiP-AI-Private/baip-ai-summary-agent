# OpenAI Data Test Script - Multi-Method Comparison

## Purpose
This script (`test_openai_data.py`) tests multiple scraping methods and compares their results. It pulls raw, unfiltered data from OpenAI's X.com profile using different approaches and saves the results to a text file for inspection.

## Features
- **Multi-Method Testing**: Tests Playwright, Scrapfly, and Nitter methods
- **Method Comparison**: Shows which methods work and their data quality
- **No Date Filtering**: Pulls recent tweets regardless of date (typically last 7-14 days worth)
- **Detailed Metadata**: Includes engagement metrics, user info, hashtags, URLs, mentions
- **Separate Sections**: Clear breakdown showing results from each method
- **Rich Output**: Formatted text file with comprehensive analysis

## Scraping Methods Tested

### 1. **Playwright Method** (Primary)
- **Technology**: Headless browser automation
- **Approach**: Captures background XHR requests from X.com
- **Advantages**: Most reliable, gets latest data, structured JSON
- **Requirements**: `playwright` package + browser installation

### 2. **Scrapfly Method** (Advanced)
- **Technology**: Professional scraping service with anti-detection
- **Approach**: Cloud-based browser automation with proxy rotation
- **Advantages**: Superior anti-detection, residential proxies, high success rate
- **Requirements**: `scrapfly-sdk` package + API key

### 3. **Nitter Method** (Fallback)
- **Technology**: Alternative Twitter frontend scraping
- **Approach**: HTML parsing from public Nitter instances
- **Advantages**: No API requirements, lightweight
- **Requirements**: `requests` + `beautifulsoup4` packages

## Usage

### Basic Usage
```bash
cd scripts
python test_openai_data.py
```

### Optional: Scrapfly API Key
For the Scrapfly method, add to your `.env` file:
```bash
SCRAPFLY_API_KEY=your_scrapfly_api_key_here
```
*(If not provided, Scrapfly method will be skipped)*

### What It Does
1. **Tests All Methods**: Runs Playwright, Scrapfly, and Nitter in sequence
2. **Compares Results**: Shows success/failure and tweet counts for each method
3. **Extracts Full Data**: No filtering by date or content  
4. **Saves Comparison**: Creates detailed file with separate sections per method
5. **Provides Analysis**: Summary stats and method effectiveness comparison

### Sample Output
```
OpenAI Data Test Scraper - Multi-Method Comparison
============================================================
This script tests multiple scraping methods and compares results.

🎭 Testing Playwright method...
  ✓ Playwright: Found 42 tweets

🚀 Testing Scrapfly method...
  ✓ Scrapfly: Found 38 tweets

🔄 Testing Nitter fallback method...
  ⚠ Nitter: No tweets found

📊 Results Summary:
  Playwright: 42 tweets
  Scrapfly:   38 tweets  
  Nitter:     0 tweets
  Total:      80 tweets

✓ Success! Multi-method comparison saved to: openai_scraped_data_20250528_163045.txt
```

### Output File Structure
```
OpenAI X.com Profile - Raw Scraped Data
Generated: 2025-05-28 16:30:00
Total Tweets: 42
Data Source: Playwright (X.com)
================================================================================
SUMMARY
================================================================================
Date Range: 2025-05-21 to 2025-05-28
Days Covered: 8
Total Likes: 125,430
Total Retweets: 18,520
Average Likes per Tweet: 2,986
Average Retweets per Tweet: 441

================================================================================
DETAILED TWEET DATA
================================================================================

================================================================================
TWEET #1
================================================================================
ID: 1795123456789012345
Date: Wed May 28 14:30:24 +0000 2025
Language: en
Source: X.com

TEXT:
We're excited to announce our new GPT-4 Turbo model with improved reasoning...

ENGAGEMENT:
  Likes: 8,432
  Retweets: 1,256
  Replies: 423
  Quotes: 89
  Views: 156,789

USER INFO:
  Username: @OpenAI
  Display Name: OpenAI
  Verified: True
  Followers: 2,156,789

HASHTAGS: AI, GPT4, Innovation

URLS:
  - https://openai.com/blog/gpt-4-turbo-update

MENTIONS: @sama, @gdb
```

## Dependencies

### Required (Always)
- **Python 3.7+**
- **dotenv** - Environment variable loading
- **asyncio** - Async execution support

### Method-Specific Dependencies

#### For Playwright Method
```bash
pip install playwright jmespath
playwright install chromium
```

#### For Scrapfly Method  
```bash
pip install scrapfly-sdk
# Plus API key: SCRAPFLY_API_KEY=your_key_here
```

#### For Nitter Method
```bash
pip install requests beautifulsoup4
```

### Install All Dependencies
```bash
pip install -r requirements.txt
playwright install chromium
```

## Output Location
Files are saved to the repository root directory:
- `../openai_scraped_data_YYYYMMDD_HHMMSS.txt`

## Use Cases

### **Method Comparison**
- **Performance Testing**: See which methods work in your environment
- **Reliability Assessment**: Compare success rates and data quality
- **Speed Analysis**: Identify fastest scraping approach

### **Data Quality Analysis**
- **Content Comparison**: See if methods return different tweet sets
- **Engagement Metrics**: Compare like/retweet counts between sources
- **Data Completeness**: Check which method provides most detailed metadata

### **Development & Debugging**
- **API Testing**: Verify scraping setup before main deployment
- **Filter Development**: Review raw data before applying date filters
- **Error Diagnosis**: Identify which methods fail and why

### **Research & Intelligence**
- **Content Analysis**: Study OpenAI's posting patterns across time
- **Engagement Research**: Analyze which content performs best
- **Timeline Analysis**: Review posting frequency and optimal timing

## Configuration

### Environment Variables (Optional)
```bash
# Required only for Scrapfly method
SCRAPFLY_API_KEY=your_scrapfly_api_key_here

# Optional: Custom proxy settings
PROXY_URL=http://your-proxy:port
```

### Method Priority
The script tests methods in this order:
1. **Playwright** (if available)
2. **Scrapfly** (if API key provided)
3. **Nitter** (if other dependencies available)

## Troubleshooting

### Common Issues

#### **"Playwright not available"**
```bash
pip install playwright
playwright install chromium
```

#### **"Scrapfly not available"**
```bash
pip install scrapfly-sdk
# Add SCRAPFLY_API_KEY to .env file
```

#### **"No tweets found from any method"**
- Check internet connectivity
- Verify X.com is accessible
- Try running at different times (rate limiting)
- Check logs in `../openai_test_scraper.log`

#### **"Scrapfly API key missing"**
- Get API key from [Scrapfly.io](https://scrapfly.io)
- Add `SCRAPFLY_API_KEY=your_key` to `.env` file
- Restart script

### Debug Information
- Check `../openai_test_scraper.log` for detailed error logs
- Each method failure is logged with specific error details
- Output file shows which methods succeeded/failed

## Method Comparison Guide

### **When to Use Each Method**

#### **Playwright** ✅ Recommended
- **Best for**: Regular monitoring, development testing
- **Pros**: Free, reliable, gets latest data structure
- **Cons**: Requires browser installation, may be blocked

#### **Scrapfly** 🚀 Professional  
- **Best for**: Production environments, high-volume scraping
- **Pros**: Superior anti-detection, residential proxies, high success rate
- **Cons**: Requires paid API key, external dependency

#### **Nitter** 🔄 Emergency Fallback
- **Best for**: When other methods are blocked
- **Pros**: Alternative data source, lightweight
- **Cons**: Often unreliable, limited data quality

This comprehensive testing script helps you choose the best scraping approach for your specific needs and environment.

