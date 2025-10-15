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
├── mcp_servers/           # MCP servers for external services
│   ├── gmail_server.py    # Gmail MCP server
│   └── notion_server.py   # Notion MCP server
├── workflows/             # LangGraph workflows
│   └── job_sync_workflow.py # Main job sync workflow
├── agent/                 # Main automation agents
│   ├── gmail_client.py    # Gmail API client
│   ├── credentials.json   # Gmail OAuth credentials (download from Google Cloud Console)
│   ├── token.json         # OAuth token (auto-generated)
│   ├── notion_utils.py    # Notion database operations
│   ├── main.py            # Daily sync orchestrator (MCP + LangGraph)
│   └── weekly_report.py   # Weekly summary generator
├── pyproject.toml         # Project configuration
├── requirements.txt       # Python dependencies
├── uv.lock                # Locked dependencies
├── README.md              # Project overview and quick start
└── SETUP_ENV.md           # Complete setup guide (includes weekly reports)
```

### Data Flow

```
Gmail API → LangGraph Workflow → Notion API
```

- ✅ **MCP Architecture**: Modular, reusable services
- ✅ **LangGraph Workflow**: Intelligent email processing with built-in deduplication
- ✅ **Single LLM Call**: Processes all emails together for better context
- ✅ **Smart Deduplication**: LLM naturally understands email relationships
- ✅ **Extensible**: Easy to add new services and workflows

## Setup

### 0. Prerequisites

**⚠️ IMPORTANT:** Before running JobSync, you need to download Gmail OAuth credentials:

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable Gmail API
4. Create OAuth 2.0 credentials
5. Download the JSON file and rename it to `credentials.json`
6. Place it in the `agent/` folder

See `SETUP_ENV.md` for detailed step-by-step instructions.

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
4. Download JSON → Save as `agent/credentials.json`
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
OPENROUTER_KEY=your_openrouter_api_key
OPENROUTER_MODEL=anthropic/claude-3.5-sonnet

# Gmail OAuth (credentials.json required in agent/)
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
2. Process all emails together with AI for intelligent deduplication
3. Extract job application info with built-in duplicate detection
4. Create entries in your Notion database
5. Handle status updates automatically

**On first run:** A browser will open for Gmail OAuth authentication. Grant permissions and the agent will save a `token.json` for future use.

**⚠️ Prerequisites:**

- You need to download `credentials.json` from Google Cloud Console and place it in the `agent/` folder
- See `SETUP_ENV.md` for detailed setup instructions

**Key improvements:**

- **Smart Deduplication**: LLM processes all emails together, naturally identifying related emails
- **Status Progression**: Automatically handles Applied → Assessment → Interview → Offer flows
- **No Duplicates**: Same company emails are merged into single applications

### Generate Weekly Report

**Note:** Requires Weekly Reports database setup (see `SETUP_ENV.md`).

```bash
uv run agent/weekly_report.py
```

## Troubleshooting

### "credentials.json not found" Error

If you see this error:

```
credentials.json not found at agent/credentials.json
```

**Solution:**

1. Download OAuth credentials from Google Cloud Console
2. Rename the file to `credentials.json`
3. Place it in the `agent/` folder
4. Run the command again

### "ModuleNotFoundError" Errors

If you see import errors:

```bash
# Clear Python cache
uv run python -c "import sys; print('Python path:', sys.path)"
# Or reinstall dependencies
uv sync
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

## Scheduling

### 🚀 GitHub Actions (Recommended - Cloud-based)

Automate everything with GitHub Actions - no need to keep your computer running!

**✨ Features:**

- ☁️ Runs in the cloud (free for public repos)
- 📅 Daily sync + weekly reports
- 🔄 Auto-refreshes OAuth tokens
- 💾 Persists cache between runs
- 📧 Email notifications on failures

**Setup (GitHub Actions):**

- Run once locally: `uv run agent/main.py` (creates `agent/token.json`)
- Add GitHub Secrets with raw JSON content (Settings → Secrets → Actions):
  - `GMAIL_CREDENTIALS` = contents of `agent/credentials.json`
  - `GMAIL_TOKEN` = contents of `agent/token.json`
  - `NOTION_TOKEN`, `NOTION_DATABASE_ID`, `NOTION_WEEKLY_REPORTS_DB_ID`, `OPENROUTER_KEY`
- Ensure workflow permissions: Settings → Actions → General → Read and write
- Manually run each workflow once to verify

See “GitHub Actions Setup” in `SETUP_ENV.md` for details.

**Schedules:**

- **Daily Sync**: Every day at 9:00 AM UTC
- **Weekly Report**: Every Monday at 10:00 AM UTC

---

### 💻 Local Scheduling (Alternative)

If you prefer running locally on your own machine:

#### Daily Sync

**Windows (Task Scheduler):**

```powershell
schtasks /create /tn "JobSync-Daily" /tr "uv run D:\Projects\JobSync\agent\main.py" /sc daily /st 09:00
```

**Linux/Mac (Cron):**

```bash
crontab -e
# Add: 0 9 * * * cd /path/to/JobSync && uv run agent/main.py
```

#### Weekly Reports

**Windows (Task Scheduler):**

```powershell
schtasks /create /tn "JobSync-Weekly" /tr "uv run D:\Projects\JobSync\agent\weekly_report.py" /sc weekly /d MON /st 10:00
```

**Linux/Mac (Cron):**

```bash
crontab -e
# Add: 0 10 * * 1 cd /path/to/JobSync && uv run agent/weekly_report.py
```

#### Using Python schedule library

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
