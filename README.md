# JobSync

Automatically track job applications from Gmail to Notion using AI-powered email parsing.

## Features

- 📧 **Gmail Integration**: Fetches recent job application emails
- 🤖 **AI Email Parsing**: Uses LLM to extract structured data from emails
- 📊 **Notion Database**: Automatically creates entries in your Notion job tracker
- 🔄 **Daily Sync**: Prevents duplicate entries with smart caching
- 🔁 **Smart Retry Logic**: Automatically handles OpenRouter rate limits with backoff
- 🎯 **Application ID Tracking**: Updates existing entries when status changes
- 📈 **Weekly Reports**: AI-generated summaries with statistics and insights

## Architecture

### Project Structure

```
JobSync/
├── gmail_mcp/             # Gmail API integration
│   ├── gmail_client.py    # Gmail API client
│   └── token.json         # OAuth token (auto-generated)
├── agent/                 # Main automation agents
│   ├── gmail_connector.py # Fetches emails from Gmail
│   ├── notion_utils.py    # Notion database operations (REST API)
│   ├── llm_utils.py       # LLM email parsing
│   ├── cache_utils.py     # Prevents duplicate processing
│   ├── cache.json         # Cache of processed emails
│   ├── main.py            # Daily sync orchestrator
│   └── weekly_report.py   # Weekly summary generator
├── pyproject.toml         # Project configuration
├── requirements.txt       # Python dependencies
├── uv.lock                # Locked dependencies
├── README.md              # Project overview and quick start
└── SETUP_ENV.md           # Complete setup guide (includes weekly reports)
```

### Data Flow

```
Gmail API → Python Agent (with LLM) → Notion REST API
```

- ✅ Simple and direct
- ✅ Perfect for automated scripts
- ✅ No extra servers needed
- ✅ Runs as scheduled task (daily/weekly)

## Setup

### 1. Install Dependencies

```bash
uv sync
# or
pip install -r requirements.txt
```

### 2. Configure Gmail API

**⚠️ IMPORTANT:** Use **Desktop app** OAuth client type (not Web application)!

Quick setup:

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Enable **Gmail API**
3. Create OAuth 2.0 Client ID → Choose **Desktop app**
4. Download JSON → Save as `gmail_mcp/credentials.json`
5. Done! (Desktop app allows `http://localhost` automatically)

**📖 Detailed setup guide:** See [`SETUP_ENV.md`](./SETUP_ENV.md)

**Common errors:**

- `redirect_uri_mismatch` → You created Web app instead of Desktop app
- `Error 403: access_denied` → Add your email as a test user in OAuth consent screen

### 3. Configure Notion

1. Go to [Notion Integrations](https://www.notion.so/my-integrations)
2. Click **+ New integration**
3. Give it a name (e.g., "JobSync")
4. Copy the **Internal Integration Token**

**Create two databases:**

**Database 1: Job Applications**

- **Title** (Title) - Auto-generated from company + job title
- **Company** (Text)
- **Job Title** (Text)
- **Status** (Select: Applied, Interview, Offer, Rejected, Assessment)
- **Applied On** (Date)
- **Notes** (Text)
- **Application ID** (Text) - Optional, for tracking reference numbers

**Database 2: Weekly Reports**

- **Name** (Title) - Report title
- **Week Range** (Text) - Date range (e.g., "Oct 5 – Oct 12")
- **Summary** (Text) - AI-generated markdown summary
- **Created On** (Date) - Report creation date

5. Share both databases with your integration:
   - Click **...** on each database → **Add connections**
   - Select your integration

### 4. Configure LLM (OpenRouter)

1. Go to [OpenRouter](https://openrouter.ai/)
2. Create an account and get an API key
3. Add credits to your account

### 5. Set Environment Variables

Create a `.env` file in the project root:

```env
# Notion Configuration
NOTION_TOKEN=your_notion_integration_token
NOTION_DATABASE_ID=your_job_applications_database_id
NOTION_WEEKLY_REPORTS_DB_ID=your_weekly_reports_database_id

# OpenRouter LLM Configuration
OPENROUTER_API_KEY=your_openrouter_api_key
OPENROUTER_MODEL=anthropic/claude-3.5-sonnet

# Gmail OAuth (credentials.json required in gmail_mcp/)
```

**To get database IDs:**

1. Open each database as a full page in Notion
2. Copy the ID from the URL: `https://www.notion.so/YOUR_DATABASE_ID?v=...`
3. The database ID is the 32-character string (no dashes)

## Usage

### Test Notion Connection

```bash
uv run agent/notion_utils.py
```

### Run Daily Sync

```bash
uv run agent/main.py
```

This will:

1. Fetch recent emails (last 10 emails by default)
2. Parse them with AI to extract job application info
3. Create entries in your Notion database
4. Cache processed emails to avoid duplicates

**On first run:** A browser will open for Gmail OAuth authentication. Grant permissions and the agent will save a `token.json` for future use.

### Generate Weekly Report

**Note:** Requires Weekly Reports database setup (see `SETUP_ENV.md`).

```bash
uv run agent/weekly_report.py
```

This will:

1. Fetch all applications from the last 7 days
2. Aggregate statistics (applications, interviews, offers, rejections)
3. Detect deadlines and action items from notes
4. Generate AI-powered 5-bullet summary with insights
5. Create a new page in your "Weekly Reports" Notion database

**Custom time range:**

```bash
uv run agent/weekly_report.py 14  # Last 14 days
uv run agent/weekly_report.py 30  # Last 30 days (monthly report)
```

## Troubleshooting

### Gmail OAuth Errors

If you see redirect URI errors:

- Make sure all redirect URIs are added in Google Cloud Console
- The code will try multiple ports and fallback to manual auth if needed
- Just follow the console prompts

### Notion API Errors

- Verify your integration token is correct
- Make sure the database is shared with your integration
- Check that property names match exactly (case-sensitive)

### LLM Parsing Errors

- Make sure OpenRouter API key has credits
- The model will try to extract: company, job_title, status, application_date
- If parsing fails, it skips that email (check console output)

### Rate Limit Handling

The agent automatically handles OpenRouter rate limits:

- **Automatic Retry**: Detects 429 errors and retries with backoff
- **Retry Schedule**: 10s → 20s → 30s delays between attempts
- **Max Attempts**: 3 retries before skipping the email
- **Console Output**: Shows `[RATE LIMIT]` messages during retries

**Example output:**

```
[RATE LIMIT] Attempt 1/3 failed. Retrying in 10s...
[RATE LIMIT] Attempt 2/3 failed. Retrying in 20s...
[OK] Application found: Amazon - SDE
```

**Tips to avoid rate limits:**

- Use a paid OpenRouter key for higher limits
- Process emails in smaller batches (adjust `max_results` in `main.py`)
- Run during off-peak hours

## Scheduling

### Daily Sync (Recommended)

Run the daily sync every morning to process new job application emails:

**Windows (Task Scheduler):**

```powershell
schtasks /create /tn "JobSync-Daily" /tr "uv run D:\Projects\JobSync\agent\main.py" /sc daily /st 09:00
```

**Linux/Mac (Cron):**

```bash
crontab -e
# Add: 0 9 * * * cd /path/to/JobSync && uv run agent/main.py
```

### Weekly Reports (Optional)

Generate a weekly summary every Monday morning:

**Windows (Task Scheduler):**

```powershell
schtasks /create /tn "JobSync-Weekly" /tr "uv run D:\Projects\JobSync\agent\weekly_report.py" /sc weekly /d MON /st 10:00
```

**Linux/Mac (Cron):**

```bash
crontab -e
# Add: 0 10 * * 1 cd /path/to/JobSync && uv run agent/weekly_report.py
```

### Using schedule library

```python
import schedule
import time

schedule.every().day.at("09:00").do(daily_sync)

while True:
    schedule.run_pending()
    time.sleep(3600)
```

## License

MIT
