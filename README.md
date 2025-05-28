# Daily AI Summary Agent 🤖📰

This project delivers automated daily summaries of the latest breakthroughs, product launches, and strategic moves from top AI companies like OpenAI, Anthropic, xAI, Google DeepMind, and more.

Powered by multiple scraping approaches and AI-generated summaries, the system automatically monitors company posts on X (Twitter) and delivers intelligent insights to your Slack channel.

## 📁 Directory Structure

```
ai-summary-agent/
├── .env                          # Environment variables (not in git)
├── .env.example                  # Environment template
├── .gitignore                    # Git ignore rules
├── README.md                     # This file
├── requirements.txt              # Python dependencies
├── TWITTER_SCRAPER_SUMMARY.md   # Implementation overview
├── .github/                     # GitHub Actions workflows
│   ├── workflows/
│   │   ├── daily-summary.yml    # Main automated workflow
│   │   └── fallback-summary.yml # Backup notification workflow
│   └── WORKFLOW_UPDATES.md      # Workflow documentation
└── scripts/                     # All scripts and utilities
    ├── twitter_scraper_scrapfly.py      # 🎯 Modern Playwright-based scraper
    ├── twitter_scraper_nitter.py        # 🔄 Nitter-based scraper (legacy)
    ├── twitter_scraper_fallback.py      # 🆘 Minimal fallback scraper
    ├── ai_summary_agent.py              # Alternative implementation
    ├── test_setup.py                    # Setup verification script
    ├── setup.sh                         # Installation script
    ├── README_scrapfly.md               # Scrapfly method documentation
    └── README_nitter.md                 # Nitter method documentation
```

## 🛠️ Technology Stack & Scraper Implementations

### **twitter_scraper_scrapfly.py** (Recommended)
**Technology:** Modern browser automation approach
- **Playwright** - Headless browser automation for JavaScript-heavy sites
- **Background Request Capture** - Intercepts X.com's internal API calls
- **JMESPath** - Advanced JSON parsing and data extraction
- **Async/Await Architecture** - Modern Python concurrency
- **Anti-Detection** - Mimics real browser behavior to avoid blocking

**Advantages:**
- Most reliable and up-to-date data
- Gets structured JSON with engagement metrics
- Handles X.com's dynamic loading
- Less likely to be blocked

### **twitter_scraper_nitter.py** (Legacy)
**Technology:** Alternative frontend scraping
- **BeautifulSoup4** - HTML parsing and scraping
- **Multiple Nitter Instances** - Uses various public Nitter servers
- **Fallback Mechanism** - Automatic instance switching on failure
- **Date Range Filtering** - UTC timezone-aware tweet filtering
- **Rate Limiting** - Delays between requests to avoid blocking

**Advantages:**
- No browser dependencies
- Lightweight and fast
- Works without JavaScript execution

## 🚀 Quick Start

### 1. Clone and Setup
```bash
git clone <repository-url>
cd ai-summary-agent
pip install -r requirements.txt
```

### 2. Install Browser Dependencies (for Scrapfly method)
```bash
playwright install chromium
playwright install-deps chromium
```

### 3. Configure Environment
```bash
cp .env.example .env
# Edit .env with your API keys (see setup sections below)
```

### 4. Test Setup
```bash
cd scripts
python test_setup.py
```

### 5. Run the Script
```bash
# Recommended: Modern Playwright-based scraper
python twitter_scraper_scrapfly.py

# Alternative: Nitter-based scraper
python twitter_scraper_nitter.py
```

## ⚙️ Configuration

### Required Environment Variables

Create a `.env` file in the root directory with:

```bash
OPENAI_API_KEY=your_openai_api_key_here
SLACK_WEBHOOK_URL=your_slack_webhook_url_here
```

## 🔧 Setting Up OpenAI API

### 1. Create an OpenAI Account
- Go to [https://platform.openai.com/signup](https://platform.openai.com/signup) and create an account, or sign in if you already have one.

### 2. Generate an API Key
- Visit the [API keys page](https://platform.openai.com/api-keys).
- Click on **"Create new secret key"**.
- Copy the generated key. This is your `OPENAI_API_KEY`.

### 3. Add to Environment
Add the key to your `.env` file:
```bash
OPENAI_API_KEY=sk-proj-your-key-here
```

**⚠️ Important:** Keep your API key private. Never commit it to version control.

## 📱 Setting Up Slack Webhook

### 1. Create a Slack Webhook
1. Go to your Slack workspace
2. Visit: https://api.slack.com/apps → **Create New App**
3. Select **"From scratch"**
4. Add **Incoming Webhooks** under Features
5. **Activate Incoming Webhooks**
6. **Add new Webhook** to your workspace and select the target channel
7. Copy the Webhook URL (e.g., `https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXXXXXX`)

### 2. Add to Environment
Add the webhook URL to your `.env` file:
```bash
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

## 🏃‍♂️ Usage

### Main Scripts
Run the daily AI summary scraper:
```bash
cd scripts

# Recommended: Modern Playwright-based scraper
python twitter_scraper_scrapfly.py

# Alternative: Nitter-based scraper  
python twitter_scraper_nitter.py

# Minimal fallback (emergency use)
python twitter_scraper_fallback.py
```

### Testing & Setup
```bash
cd scripts

# Verify setup and dependencies
python test_setup.py

# Install dependencies (Linux/Mac)
./setup.sh
```

## 🔍 How It Works

1. **🕷️ Data Scraping**: Multiple approaches for reliability
   - **Primary**: Playwright browser automation capturing X.com API calls
   - **Fallback**: Nitter instance scraping with HTML parsing
2. **🤖 AI Processing**: Uses OpenAI GPT to analyze and summarize content
3. **📊 Smart Categorization**: Automatically categorizes updates by type
4. **📤 Slack Delivery**: Posts formatted summaries to your configured channel
5. **🔄 Fallback System**: Multiple backup mechanisms ensure reliable operation

### Monitored Companies
- OpenAI
- xAI (Elon Musk's AI company)
- Anthropic
- Google DeepMind
- Mistral AI
- Meta AI
- Cohere
- Perplexity AI
- Scale AI
- Runway ML
- DAIR.AI

## 🤖 How OpenAI Powers the Intelligence

OpenAI serves as the **core intelligence engine** that transforms raw scraped tweet data into coherent, actionable daily summaries.

### **Primary Purpose: AI-Powered Tweet Summarization**

The system uses OpenAI's GPT-3.5-turbo to analyze and synthesize social media content from major AI companies into business intelligence.

### **Technical Implementation**

#### **Client Initialization**
```python
from openai import OpenAI
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)
```

#### **Summary Generation Process**
1. **Input Processing**: Collects tweets from monitored AI companies
2. **Prompt Engineering**: Uses structured prompts to guide analysis
3. **API Call**: Processes content through GPT-3.5-turbo
4. **Output Formatting**: Delivers structured summaries

#### **Prompt Engineering**
The system uses carefully crafted prompts to extract business value:
```python
prompt = """Analyze these tweets from AI companies and create a concise daily summary:

Key points to extract:
- New product announcements
- Technical breakthroughs  
- Important partnerships
- Notable research findings
- Significant company updates
- Industry trends and insights

Please format the summary in clear bullet points with the most important information first.
"""
```

#### **API Configuration**
```python
response = client.chat.completions.create(
    model="gpt-3.5-turbo",           # Cost-effective, reliable model
    messages=[{"role": "user", "content": prompt}],
    temperature=0.3,                  # Low temperature for consistent, factual output
    max_tokens=600                    # Controlled response length
)
```

### **Multi-Layer Reliability System**

#### **Fallback Mechanisms**
1. **Primary**: Modern OpenAI Python client (v1.12.0+)
2. **Secondary**: Legacy OpenAI API compatibility
3. **Tertiary**: Manual categorization when AI is unavailable
4. **Emergency**: Basic notifications without AI processing

#### **Error Handling**
- **Quota Exceeded**: Automatically falls back to manual summary with topic categorization
- **API Errors**: Graceful degradation maintains service availability
- **Network Issues**: Continues operation without AI enhancement

### **Cost Optimization Features**

#### **Token Management**
- Limits input to 25 tweets maximum per analysis
- Uses cost-effective GPT-3.5-turbo model
- Maximum 600 tokens output to control costs
- Single API call processes all content efficiently

#### **Smart Processing**
- Batches all tweets into single analysis
- Avoids multiple API calls per company
- Efficient prompt design for comprehensive results

### **Quality Assurance**

#### **Consistent Output**
- **Low Temperature (0.3)**: Ensures factual, consistent summaries
- **Structured Prompts**: Guide specific output format and content
- **Bullet-Point Formatting**: Optimized for business readability

#### **Content Intelligence**
- **Business Focus**: Emphasizes company updates and industry developments
- **Significance Filtering**: Highlights important announcements over casual content
- **Trend Detection**: Identifies patterns across multiple companies

### **Integration Benefits**

#### **Business Intelligence Value**
OpenAI transforms raw social media monitoring into actionable insights by:
- **Synthesizing** multiple sources into coherent briefings
- **Categorizing** updates by business importance
- **Highlighting** key trends and competitive developments
- **Delivering** daily executive summaries

#### **Competitive Advantage**
Creates a **competitive intelligence system** that helps users:
- Stay ahead of fast-moving AI industry developments
- Monitor competitor announcements and strategies
- Identify emerging trends and opportunities
- Save hours of manual social media monitoring

#### **Workflow Integration**
- **Daily Automation**: Processes previous day's content automatically
- **Immediate Availability**: Summaries ready when you start your day
- **Slack Integration**: Delivers insights directly to your team
- **Manual Triggers**: On-demand analysis when needed

This AI-powered approach elevates simple social media scraping into a sophisticated business intelligence tool that provides genuine strategic value.

## 🛡️ Reliability Features

### Multi-Layer Fallback System
1. **Primary**: Playwright-based scraping with real browser
2. **Secondary**: Nitter instance scraping with automatic failover
3. **Tertiary**: Manual categorized summary when AI is unavailable
4. **Emergency**: Basic notification when all scraping fails

### Error Handling
- Graceful handling of service outages
- Comprehensive logging for debugging
- Error notifications sent to Slack
- Automatic retry mechanisms with backoff

### Robust Architecture
- Multiple scraping strategies
- Rate limiting and request throttling
- Timeout handling for network requests
- Browser automation with anti-detection

## 📋 Dependencies

Install via `pip install -r requirements.txt`:

- `openai>=1.12.0` - OpenAI API client
- `requests>=2.31.0` - HTTP requests
- `python-dotenv>=1.0.1` - Environment variable management
- `beautifulsoup4>=4.12.3` - HTML parsing (Nitter method)
- `pytz>=2024.1` - Timezone handling
- `playwright>=1.40.0` - Browser automation (Scrapfly method)
- `jmespath>=1.0.1` - JSON parsing (Scrapfly method)

## 🔧 Troubleshooting

### Common Issues

**1. "Playwright not available"**
- Install with: `pip install playwright`
- Then run: `playwright install chromium`
- For system dependencies: `playwright install-deps chromium`

**2. "No working sources found"**
- Try the Scrapfly method: `python twitter_scraper_scrapfly.py`
- Check logs for detailed error information
- Verify network connectivity

**3. "OpenAI quota exceeded"**
- The script will fall back to manual summarization
- Check your OpenAI billing and usage limits
- Consider upgrading your OpenAI plan

**4. "Slack webhook failed"**
- Verify your `SLACK_WEBHOOK_URL` is correct
- Check if the Slack app has proper permissions
- Test webhook URL directly

### Logs
Check `tweet_scraper.log` for detailed execution logs and error information.

## 🚀 Deployment Options

### GitHub Actions (Automated)
The project includes automated deployment via GitHub Actions:
- **Daily Schedule**: Runs automatically at 11:00 UTC
- **Manual Trigger**: Can be run on-demand
- **Fallback Workflow**: Backup notification system

See [Workflow Documentation](.github/WORKFLOW_UPDATES.md) for details.

### Manual Execution
```bash
cd scripts && python twitter_scraper_scrapfly.py
```

### Scheduled Execution (Cron/Task Scheduler)
**Linux/Mac cron example (daily at 9 AM):**
```bash
0 9 * * * cd /path/to/ai-summary-agent/scripts && python twitter_scraper_scrapfly.py
```

## 📚 Additional Documentation

- [**Twitter Scraper Summary**](TWITTER_SCRAPER_SUMMARY.md) - Implementation overview and comparison
- [**Scrapfly Method Guide**](scripts/README_scrapfly.md) - Detailed Playwright implementation docs
- [**Nitter Method Guide**](scripts/README_nitter.md) - Legacy scraping approach documentation  
- [**Workflow Updates**](.github/WORKFLOW_UPDATES.md) - GitHub Actions configuration and changes
- [**Setup Script**](scripts/setup.sh) - Automated dependency installation

## 🤝 Contributing

This project demonstrates the power of AI automation for staying ahead of fast-moving industry trends. 

**Have suggestions?**
- Additional AI companies to monitor
- New data sources or platforms
- Feature improvements
- Bug reports

Feel free to open issues or submit pull requests!

## 📈 Future Enhancements

- Support for additional social media platforms
- Integration with RSS feeds and company blogs
- Sentiment analysis and trend detection
- Multi-language support
- Web dashboard for managing sources and viewing analytics
- Integration with other communication platforms (Discord, Teams, etc.)

---

*This is just a glimpse of how we can use AI to automate research and stay ahead of fast-moving trends. Imagine the possibilities as we extend this approach across other domains!* 🚀