# AI Business Week Summary Agent 🤖📰

**Automated AI industry intelligence gathering and reporting system**

This project automatically monitors major AI companies on X (Twitter), analyzes their latest posts using AI, and delivers intelligent weekly summaries to your Slack channel. Perfect for staying informed about the fast-moving AI industry during business hours.

## 🎯 What This Does

- **Monitors 11 Major AI Companies**: OpenAI, xAI, Anthropic, Google DeepMind, Mistral AI, Meta AI, Cohere, Perplexity, Scale AI, Runway, and DAIR.ai
- **Smart Scheduling**: Runs Tuesday-Saturday at 2:00 AM UTC (business week focus)
- **AI-Powered Analysis**: Uses OpenAI GPT to generate intelligent summaries of industry developments
- **Business Intelligence Focus**: Emphasizes product launches, partnerships, research breakthroughs, and strategic moves
- **Reliable Delivery**: Professional-grade scraping with anti-detection and fallback systems

## 🏗️ Architecture

### **Production Scraping Stack:**
- **Scrapfly SDK** (Primary) - Professional web scraping with residential proxies and anti-bot protection
- **Playwright** (Fallback) - Headless browser automation for JavaScript-heavy sites
- **Dynamic Rate Limiting** - Adaptive delays based on success/failure patterns
- **Comprehensive Error Handling** - Graceful degradation and detailed diagnostics

### **Data Processing:**
- **Advanced JSON Parsing** - Extracts structured data from X.com's internal APIs
- **Date Intelligence** - 5-day lookback window with timezone awareness
- **Content Filtering** - Focus on meaningful business developments
- **Engagement Analysis** - Prioritizes high-impact posts

### **Automation & Delivery:**
- **GitHub Actions** - Serverless execution and scheduling
- **Slack Integration** - Professional business intelligence reports
- **OpenAI Integration** - AI-generated summaries and insights

## 📁 Project Structure

```
ai-summary-agent/
├── .env.example                    # Environment template
├── .gitignore                      # Git ignore rules
├── LICENSE                         # MIT License
├── README.md                       # This file
├── requirements.txt                # Python dependencies
├── .github/workflows/              # GitHub Actions automation
│   ├── daily-summary.yml          # Main business week workflow
│   └── fallback-summary.yml       # Backup notification system
├── scripts/                        # Production code
│   ├── twitter_scraper_scrapfly.py # 🎯 Main production scraper
│   ├── twitter_scraper_fallback.py # Minimal fallback scraper
│   ├── twitter_scraper_nitter.py  # Alternative Nitter-based scraper
│   ├── ai_summary_agent.py        # Alternative implementation
│   └── setup.sh                   # Installation script
├── tests/                          # Test and debug utilities
│   ├── test_setup.py              # Environment validation
│   ├── test_simple.py             # Basic scraping test
│   ├── debug_xhr.py               # XHR debugging
│   └── debug_comprehensive.py     # Full system diagnosis
└── docs/                          # Documentation
    ├── TWITTER_SCRAPER.md          # Implementation details
    └── SCRAPFLY_INTEGRATION.md     # Scrapfly setup guide
```

## 🚀 Quick Start

### **1. Prerequisites**
- Python 3.11+
- Scrapfly API account (recommended for reliability)
- OpenAI API account
- Slack webhook URL

### **2. Local Setup**

```bash
# Clone the repository
git clone <your-repo-url>
cd ai-summary-agent

# Install dependencies
pip install -r requirements.txt

# Install browser for Playwright fallback
playwright install chromium

# Configure environment
cp .env.example .env
# Edit .env with your API keys (see Environment Setup below)
```

### **3. Environment Setup**

Create a `.env` file with your API credentials:

```bash
# Required: Slack notification endpoint
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...

# Recommended: Professional scraping (more reliable)
SCRAPFLY_API_KEY=scp-live-your_key_here

# Optional: AI-powered summaries (fallback to manual summaries)
OPENAI_API_KEY=sk-...your_key_here
```

### **4. Test Your Setup**

```bash
# Validate environment and dependencies
cd tests
python test_setup.py

# Test scraping with one account
python test_simple.py

# Full system test
cd ../scripts
python twitter_scraper_scrapfly.py
```

## 🔧 Getting API Keys

### **Scrapfly (Highly Recommended)**
1. Sign up at [https://scrapfly.io](https://scrapfly.io)
2. Get your API key from the dashboard
3. Add to `.env`: `SCRAPFLY_API_KEY=scp-live-your_key`

**Why Scrapfly?** X.com has sophisticated anti-bot detection. Scrapfly provides enterprise-grade scraping with residential proxies, making it much more reliable than basic automation.

### **Slack Webhook**
1. Go to your Slack workspace
2. Apps → Incoming Webhooks → Add to Slack
3. Choose channel and copy webhook URL
4. Add to `.env`: `SLACK_WEBHOOK_URL=https://hooks.slack.com/...`

### **OpenAI (Optional)**
1. Sign up at [https://platform.openai.com](https://platform.openai.com)
2. Create an API key
3. Add to `.env`: `OPENAI_API_KEY=sk-...`

*Without OpenAI, the system generates manual summaries instead of AI-powered analysis.*

## 🤖 GitHub Actions Setup

### **1. Repository Secrets**
Add these secrets in GitHub: Settings → Secrets and variables → Actions

- `SCRAPFLY_API_KEY` - Your Scrapfly API key
- `SLACK_WEBHOOK_URL` - Your Slack webhook URL  
- `OPENAI_API_KEY` - Your OpenAI API key (optional)

### **2. Workflow Schedule**
The system runs automatically:
- **Schedule**: Tuesday-Saturday at 2:00 AM UTC
- **Coverage**: Last 5 business days of AI company activity
- **Delivery**: Professional business intelligence reports to Slack

### **3. Manual Triggers**
You can also run workflows manually:
- Go to Actions tab → Select workflow → Run workflow

## 🧪 Testing & Debugging

### **Basic Tests**
```bash
cd tests

# Environment validation
python test_setup.py

# Quick scraping test
python test_simple.py

# Test specific account
python debug_xhr.py
```

### **Advanced Debugging**
```bash
# Comprehensive system diagnosis
python debug_comprehensive.py

# XHR request analysis
python debug_xhr.py

# Scrapfly-specific debugging
python debug_scrapfly.py
```

### **Troubleshooting Common Issues**

**No tweets found:**
- Check if Scrapfly API key is valid
- Verify accounts are posting (try test_simple.py)
- Check date range (5-day window may need adjustment)

**Rate limiting:**
- The system has dynamic rate limiting built-in
- Scrapfly provides better rate limit handling than Playwright

**GitHub Actions failures:**
- Check secrets are properly configured
- Review workflow logs for specific errors
- Use fallback workflow if main workflow fails

## 📊 Understanding the Output

### **Slack Reports Include:**
- **Product Announcements** - New tools, features, and services
- **Technical Breakthroughs** - Research developments and capabilities
- **Business Developments** - Partnerships, funding, strategic moves
- **Industry Trends** - Market analysis and competitive intelligence

### **Report Format:**
```
📰 AI Business Week Summary - Tuesday, 2025-06-16

• Product Updates: Canvas now supports PDF/DOCX downloads (OpenAI)
• Technical Breakthroughs: New multimodal capabilities announced
• Business Intelligence: Major partnership between Company X and Y
• Industry Trends: Growing focus on enterprise AI solutions

_Scraped 24 tweets from 11 AI companies (last 5 days)_
```

## 🔀 Alternative Scraping Methods

The system includes multiple scraping approaches:

1. **Scrapfly** (Recommended) - Professional service with anti-detection
2. **Playwright** (Fallback) - Direct browser automation
3. **Nitter** (Legacy) - Alternative frontend scraping

If one method fails, the system automatically falls back to the next available option.

## 🤝 Contributing

### **Development Setup**
```bash
# Install development dependencies
pip install -r requirements.txt
playwright install chromium

# Run tests
cd tests
python test_setup.py

# Test changes
python test_simple.py
```

### **Adding New Companies**
Edit `X_ACCOUNTS` list in `scripts/twitter_scraper_scrapfly.py`:
```python
X_ACCOUNTS = ["OpenAI", "xai", "AnthropicAI", "YourNewCompany"]
```

### **Customizing Summaries**
Modify the AI prompt in the `generate_summary()` method to focus on different aspects of AI industry developments.

## 📋 System Requirements

- **Python**: 3.11 or higher
- **Memory**: 512MB+ (for browser automation)
- **Network**: Stable internet connection
- **Storage**: 100MB for dependencies

## 🔒 Security & Privacy

- **No Data Storage**: Tweets are processed in memory only
- **API Key Security**: Use environment variables and GitHub secrets
- **Rate Limiting**: Respectful of platform limits
- **Error Handling**: Graceful failure without exposing credentials

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

**Common Issues:**
- Check the [tests/](tests/) directory for debugging tools
- Review GitHub Actions logs for automation issues
- Verify all API keys are correctly configured

**Need Help?**
- Check the [docs/](docs/) directory for detailed guides
- Review test outputs for specific error messages
- Ensure all dependencies are properly installed

---

*This system provides automated AI industry intelligence gathering for business professionals who need to stay informed about the rapidly evolving artificial intelligence landscape.*
