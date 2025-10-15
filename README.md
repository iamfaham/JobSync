# JobSyncd

AI-powered, intelligent automation for job application tracking using LLMs and MCPs.

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
JobSyncd/
├── mcp_servers/           # MCP servers for external services
│   ├── gmail_server.py    # Gmail MCP server
│   ├── notion_server.py   # Notion MCP server
│   └── weekly_report_server.py # Weekly report MCP server
├── workflows/             # LangGraph workflows
│   ├── job_sync_workflow.py # Main job sync workflow
│   └── weekly_report_workflow.py # Weekly report workflow
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

- ✅ **MCP Architecture**: Modular, reusable services
- ✅ **LangGraph Workflow**: Intelligent email processing with built-in deduplication
- ✅ **Single LLM Call**: Processes all emails together for better context
- ✅ **Smart Deduplication**: LLM naturally understands email relationships
- ✅ **Extensible**: Easy to add new services and workflows

## Setup

See [`SETUP_ENV.md`](./SETUP_ENV.md) for complete setup instructions including Gmail API, Notion configuration, and environment variables.

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

**Prerequisites:**

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

This will:

1. Fetch application data from the last 7 days using MCP + LangGraph
2. Generate AI-powered summary with intelligent insights
3. Create a formatted report in your Notion database
4. Handle rate limits and errors gracefully

**Custom time range:**

```bash
uv run agent/weekly_report.py 14  # Last 14 days
uv run agent/weekly_report.py 30  # Last 30 days (monthly report)
```

**Key improvements:**

- **MCP Architecture**: Modular, reusable weekly report services
- **LangGraph Workflow**: Intelligent data processing and summary generation
- **Smart Insights**: AI analyzes patterns and provides actionable recommendations
- **Flexible Timeframes**: Support for custom date ranges

## Scheduling

### GitHub Actions (Recommended - Cloud-based)

Automate everything with GitHub Actions - no need to keep your computer running!

**Features:**

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

### Local Scheduling (Alternative)

If you prefer running locally on your own machine:

#### Daily Sync

**Windows (Task Scheduler):**

```powershell
schtasks /create /tn "JobSyncd-Daily" /tr "uv run D:\Projects\JobSyncd\agent\main.py" /sc daily /st 09:00
```

**Linux/Mac (Cron):**

```bash
crontab -e
# Add: 0 9 * * * cd /path/to/JobSyncd && uv run agent/main.py
```

#### Weekly Reports

**Windows (Task Scheduler):**

```powershell
schtasks /create /tn "JobSyncd-Weekly" /tr "uv run D:\Projects\JobSyncd\agent\weekly_report.py" /sc weekly /d MON /st 10:00
```

**Linux/Mac (Cron):**

```bash
crontab -e
# Add: 0 10 * * 1 cd /path/to/JobSyncd && uv run agent/weekly_report.py
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

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for more details.
