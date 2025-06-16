# Tests Directory

This directory contains test and debugging utilities for the AI Summary Agent.

## Test Files

### **Setup & Validation**
- `test_setup.py` - Validates environment configuration and dependencies
- `test_simple.py` - Basic scraping test with one AI company
- `test_scraper.py` - Test scraper functionality and recent tweet filtering

### **Debugging Tools**
- `debug_xhr.py` - Debug XHR requests captured by Scrapfly
- `debug_comprehensive.py` - Full system diagnosis with detailed output
- `debug_scraper.py` - Debug scraper behavior and rate limiting
- `debug_scrapfly.py` - Scrapfly-specific debugging
- `simple_debug.py` - Simple debugging without complex formatting

### **Data Analysis**
- `test_openai_data.py` - Compare different scraping methods and data quality

## Usage

Run tests from the tests directory:

```bash
cd tests

# Basic environment check
python test_setup.py

# Quick functionality test
python test_simple.py

# Debug scraping issues
python debug_xhr.py
```

## Troubleshooting

**Import errors:**
- Ensure you're running from the tests directory
- Check that scripts directory exists and contains the main scraper files

**No tweets found:**
- Run `debug_xhr.py` to see what XHR requests are being captured
- Check API keys are properly configured
- Verify Scrapfly account has sufficient credits

**Rate limiting:**
- Use `debug_scraper.py` to test dynamic rate limiting
- Check Scrapfly dashboard for usage limits
