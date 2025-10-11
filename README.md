# JobTracker

Automatically track job applications from Gmail to Notion using AI-powered email parsing.

## Features

- 📧 **Gmail Integration**: Fetches recent job application emails
- 🤖 **AI Email Parsing**: Uses LLM to extract structured data from emails
- 📊 **Notion Database**: Automatically creates entries in your Notion job tracker
- 🔄 **Daily Sync**: Prevents duplicate entries with smart caching
- 🔁 **Smart Retry Logic**: Automatically handles OpenRouter rate limits with backoff
- 🎯 **Application ID Tracking**: Updates existing entries when status changes
- 📈 **Weekly Reports**: AI-generated summaries with statistics and insights
- 🛠️ **MCP Server**: Exposes Gmail data via Model Context Protocol (optional)

## Architecture

### Project Structure

```
JobTracker/
├── gmail_mcp/             # Gmail MCP server (optional - for AI tools)
│   ├── gmail_client.py    # Gmail API client
│   ├── gmail_server.py    # MCP server exposing Gmail tools
│   └── gmail_utils.py     # Utilities & test functions
├── agent/                 # Main automation agents
│   ├── gmail_connector.py # Fetches emails
│   ├── notion_utils.py    # Notion database operations (REST API)
│   ├── llm_utils.py       # LLM email parsing
│   ├── cache_utils.py     # Prevents duplicates
│   ├── main.py            # Daily sync orchestrator
│   └── weekly_report.py   # Weekly summary generator
├── notion_mcp_server.py   # Optional: MCP server for Notion DB
├── README.md              # Project overview and quick start
└── SETUP_ENV.md           # Complete setup guide (includes weekly reports)
```

### Data Flow Options

**Option 1: Direct (Current - Recommended for automation)**

```
Gmail API → Python Agent (with LLM) → Notion REST API
```

- ✅ Simple and direct
- ✅ Perfect for automated scripts
- ✅ No extra servers needed

**Option 2: Via MCP (For AI tool integration)**

```
Gmail API → Python Agent (with LLM) → Your Notion MCP Server → Notion REST API
                                      ↑
Claude Desktop / Other AI Tools ──────┘
```

- ✅ Allows Claude Desktop to write to your DB
- ✅ Reusable across multiple AI tools
- ❌ More complex setup

**Option 3: Using Notion's Hosted MCP (Separate from this project)**

```
Claude Desktop → Notion MCP (hosted by Notion) → Your Notion Workspace
```

- ✅ Official Notion integration
- ✅ No setup required
- ⚠️ Separate from your Python agent

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

**🔍 Verify setup:**

```bash
uv run gmail_mcp/verify_credentials.py
```

**Common errors:**

- `redirect_uri_mismatch` → You created Web app instead of Desktop app
- `Error 403: access_denied` → Add your email as a test user in OAuth consent screen

See [`GMAIL_OAUTH_SETUP.md`](./GMAIL_OAUTH_SETUP.md) for solutions.

### 3. Configure Notion

1. Go to [Notion Integrations](https://www.notion.so/my-integrations)
2. Click **+ New integration**
3. Give it a name (e.g., "JobTracker")
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

### Test Gmail Connection

```bash
uv run gmail_mcp/gmail_utils.py
```

On first run, it will:

1. Try to open a browser for OAuth
2. Ask you to authorize the app
3. Save a `token.json` for future use

### Test Notion Connection

```bash
uv run agent/notion_utils.py
```

### Run Daily Sync

```bash
uv run agent/main.py
```

This will:

1. Fetch recent emails (last 7 days)
2. Parse them with AI to extract job application info
3. Create entries in your Notion database
4. Cache processed emails to avoid duplicates

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

### Run MCP Servers (Optional)

#### Gmail MCP Server

Allows AI tools like Claude Desktop to access your Gmail:

```bash
uv run gmail_mcp/gmail_server.py
```

#### Notion MCP Server

Allows AI tools to write to your job tracker database:

```bash
uv run notion_mcp_server.py
```

#### Configure in Claude Desktop

Add to your Claude Desktop config (`%APPDATA%\Claude\claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "gmail": {
      "command": "uv",
      "args": ["run", "gmail_mcp/gmail_server.py"],
      "cwd": "D:\\Projects\\JobTracker"
    },
    "jobtracker": {
      "command": "uv",
      "args": ["run", "notion_mcp_server.py"],
      "cwd": "D:\\Projects\\JobTracker"
    }
  }
}
```

Now Claude can:

- Read your Gmail: "Show me job application emails from the last week"
- Write to your tracker: "Add a job application for Software Engineer at Google, status: Applied"
- Query your tracker: "What jobs did I apply to this week?"

## Notion MCP (Optional)

If you want to connect Notion to AI tools, use [Notion's hosted MCP service](https://developers.notion.com/docs/get-started-with-mcp):

1. Open **Settings** in Notion app
2. Go to **Connections** → **Notion MCP**
3. Choose your AI tool and complete OAuth

This is **separate** from this project - it's for AI tools to read/write Notion directly.

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
schtasks /create /tn "JobTracker-Daily" /tr "uv run D:\Projects\JobTracker\agent\main.py" /sc daily /st 09:00
```

**Linux/Mac (Cron):**

```bash
crontab -e
# Add: 0 9 * * * cd /path/to/JobTracker && uv run agent/main.py
```

### Weekly Reports (Optional)

Generate a weekly summary every Monday morning:

**Windows (Task Scheduler):**

```powershell
schtasks /create /tn "JobTracker-Weekly" /tr "uv run D:\Projects\JobTracker\agent\weekly_report.py" /sc weekly /d MON /st 10:00
```

**Linux/Mac (Cron):**

```bash
crontab -e
# Add: 0 10 * * 1 cd /path/to/JobTracker && uv run agent/weekly_report.py
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
