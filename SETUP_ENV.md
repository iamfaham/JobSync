# Environment Variables Setup

## Quick Start

1. **Create `.env` file** in the project root:

   ```bash
   cp .env.template .env
   ```

   Or create manually

2. **Fill in the values** (see below for how to get each one)

---

## 🔑 Required Variables

### 1. NOTION_TOKEN

**What it is:** Your Notion integration token (for writing to Notion database)

**How to get it:**

1. Go to https://www.notion.so/my-integrations
2. Click **+ New integration**
3. Name it "JobSync"
4. Select the workspace
5. Click **Submit**
6. Copy the **Internal Integration Token**

**Add to `.env`:**

```env
NOTION_TOKEN=secret_xxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

---

### 2. NOTION_DATABASE_ID

**What it is:** The ID of your Notion job tracker database (Job Applications)

**How to get it:**

**Step 1: Create database in Notion with these properties:**

- **Title** (Title)
- **Company** (Text)
- **Job Title** (Text)
- **Status** (Select: Applied, Interview, Offer, Rejected, Assessment)
- **Applied On** (Date)
- **Notes** (Text)
- **Application ID** (Text)

**Step 2: Share database with your integration:**

- Open the database in Notion
- Click **...** (top right) → **Add connections**
- Select your "JobSync" integration

**Step 3: Get the database ID:**

- Open database as full page
- Copy ID from URL:
  ```
  https://www.notion.so/YOUR_DATABASE_ID?v=...
                        ^^^^^^^^^^^^^^^^^^
  ```

**Add to `.env`:**

```env
NOTION_DATABASE_ID=abcdef1234567890abcdef1234567890
```

---

### 2b. NOTION_WEEKLY_REPORTS_DB_ID

**What it is:** The ID of your Weekly Reports Notion database (for automated summaries)

**How to get it:**

**Step 1: Create a second database in Notion with these properties:**

- **Name** (Title) - Report title
- **Week Range** (Text) - Date range
- **Summary** (Text) - AI-generated summary
- **Created On** (Date) - Report date

**Step 2: Share database with your integration:**

- Open the database in Notion
- Click **...** (top right) → **Add connections**
- Select your "JobSync" integration

**Step 3: Get the database ID:**

- Open database as full page
- Copy ID from URL (same process as above)

**Add to `.env`:**

```env
NOTION_WEEKLY_REPORTS_DB_ID=1234567890abcdef1234567890abcdef
```

---

### 3. OPENROUTER_KEY

**What it is:** API key for OpenRouter (provides access to Claude/GPT models)

**How to get it:**

1. Go to https://openrouter.ai/
2. Sign up / Sign in
3. Click your profile → **Keys**
4. Click **Create Key**
5. Copy the key
6. **Add credits:** Go to **Credits** → Add $5-10 (plenty for testing)

**Add to `.env`:**

```env
OPENROUTER_KEY=sk-or-v1-xxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

---

### 4. OPENROUTER_MODEL (Optional)

**What it is:** Which AI model to use for parsing emails

**Default:** `anthropic/claude-3.5-sonnet` (best quality)

**Alternatives:**

- `anthropic/claude-3-haiku` (faster, cheaper)
- `openai/gpt-4o-mini` (cheaper)
- `openai/gpt-4o` (high quality)

**Add to `.env`:**

```env
OPENROUTER_MODEL=anthropic/claude-3.5-sonnet
```

---

### 5. Gmail API Setup (OAuth 2.0)

**What it is:** Authentication to read your Gmail inbox for job application emails

**Important:** Gmail OAuth uses `credentials.json` file (not an environment variable)

#### Step 1: Create Google Cloud Project

1. Go to https://console.cloud.google.com/
2. Click **Select a project** → **New Project**
3. Name it "JobSync" → **Create**
4. Wait for project creation (check notification bell)

#### Step 2: Enable Gmail API

1. In your project, go to **APIs & Services** → **Library**
2. Search for "Gmail API"
3. Click **Gmail API** → **Enable**

#### Step 3: Configure OAuth Consent Screen

1. Go to **APIs & Services** → **OAuth consent screen**
2. Choose **External** → **Create**
3. Fill in:
   - **App name:** JobSync
   - **User support email:** Your email
   - **Developer contact:** Your email
4. Click **Save and Continue**
5. **Scopes:** Skip this (click Save and Continue)
6. **Test users: Audience → ** Click **+ Add Users** → Add your Gmail address
   - ⚠️ **CRITICAL:** If app is in "Testing" mode, ONLY test users can access it
   - Add the exact Gmail account you want to read emails from
7. Click **Save and Continue** → **Back to Dashboard**

#### Step 4: Create OAuth 2.0 Credentials

1. Go to **APIs & Services** → **Credentials**
2. Click **+ Create Credentials** → **OAuth client ID**
3. **Application type:** Select **Desktop app** (NOT Web application)
   - ⚠️ **IMPORTANT:** Must be "Desktop app" for `http://localhost` to work
4. **Name:** JobSync Desktop
5. Click **Create**
6. Click **Download JSON** (or click the download icon ⬇️ in credentials list)

#### Step 5: Save credentials.json

1. Rename downloaded file to `credentials.json`
2. Move it to `agent/` folder in your project:
   ```
   JobSync/
   ├── agent/
   │   ├── credentials.json  ← PUT IT HERE
   │   └── gmail_client.py
   ```

#### Step 6: First-Time Authentication

1. Run the agent:

   ```bash
   cd D:\Projects\JobSync
   uv run agent/main.py
   ```

2. **A browser will open automatically** (or copy the URL shown)
3. **Sign in** with the Gmail account you added as a test user
4. **Grant permissions** (read Gmail)
5. **If you see "Google hasn't verified this app":**
   - Click **Advanced**
   - Click **Go to JobSync (unsafe)** ← This is YOUR app, it's safe
6. **Success!** You'll see "The authentication flow has completed"
7. A `token.json` file is created in `agent/` folder (keeps you logged in)

#### Common Gmail OAuth Errors

**Error: "redirect_uri_mismatch"**

- ✅ **Fix:** Make sure you created a **Desktop app**, not Web application
- Desktop apps automatically support `http://localhost`

**Error: "Error 403: access_denied"**

- ✅ **Fix:** Add your Gmail account as a Test User in OAuth consent screen
- Go to OAuth consent screen → Test users → Add your email

**Error: "[WinError 10013] Port already in use"**

- ✅ **Fix:** The code automatically tries multiple ports (8080, 49256, 8000)
- If all fail, it switches to manual authentication (copy/paste code)

**Error: "credentials.json not found"**

- ✅ **Fix:** Make sure `credentials.json` is in the `agent/` folder
- Check the file name (no extra .txt extension)

#### Gmail OAuth Files Structure

After setup, your `agent/` folder should have:

```
agent/
├── credentials.json  ← You download this (OAuth client secrets)
├── token.json        ← Auto-created after first login (keeps you logged in)
└── gmail_client.py   ← Code that uses the credentials
```

**Security Notes:**

- ✅ `credentials.json` - Client ID (safe to commit, but not recommended)
- ❌ `token.json` - Your personal login token (NEVER commit this)
- Both are in `.gitignore` for safety

---

## 📝 Complete .env Example

```env
# Notion Configuration
NOTION_TOKEN=secret_abc123xyz789
NOTION_DATABASE_ID=1234567890abcdef1234567890abcdef
NOTION_WEEKLY_REPORTS_DB_ID=abcdef1234567890abcdef1234567890

# OpenRouter LLM Configuration
OPENROUTER_KEY=sk-or-v1-xxxxxxxxxxxx
OPENROUTER_MODEL=anthropic/claude-3.5-sonnet

# Gmail OAuth (handled separately - credentials.json in agent/)
```

---

## 📊 Weekly Report Agent Setup (Optional)

The Weekly Report Agent automatically generates AI-powered summaries of your job application activity.

### Prerequisites

Before setting up weekly reports:

- ✅ Completed the main JobSync setup (Gmail, OpenRouter, Notion)
- ✅ Successfully run the daily sync agent (`agent/main.py`)
- ✅ At least a few job applications in your Notion database

### Step 1: Create Weekly Reports Database

1. **Create a new database in Notion** with these exact properties:

   | Property Name | Type  | Description                         |
   | ------------- | ----- | ----------------------------------- |
   | Name          | Title | Report title                        |
   | Week Range    | Text  | Date range (e.g., "Oct 5 – Oct 12") |
   | Summary       | Text  | AI-generated summary                |
   | Created On    | Date  | Report creation date                |

2. **Share the database with your integration:**

   - Click **...** (three dots) on the database
   - Click **Add connections**
   - Select your "JobSync" integration

3. **Get the database ID:**
   - Open the database as a full page
   - Copy the ID from the URL:
     ```
     https://www.notion.so/YOUR_DATABASE_ID?v=...
                           ^^^^^^^^^^^^^^^^^^
     ```
   - It's a 32-character string without dashes

### Step 2: Add to Environment Variables

Update your `.env` file with the Weekly Reports database ID:

```env
NOTION_WEEKLY_REPORTS_DB_ID=your_weekly_reports_db_id_here
```

### Step 3: Test the Weekly Report Agent

```bash
cd D:\Projects\JobSync
uv run agent/weekly_report.py
```

**Expected output:**

```
======================================================================
📊 WEEKLY JOB APPLICATION REPORT
======================================================================

[INFO] Generating report for: Oct 5 – Oct 12
[INFO] Fetching applications from Notion (last 7 days)...

[STATS] Weekly Statistics:
   Total Applications: 5
   📝 Applied: 3
   🎯 Interviews: 2
   ...

[OK] Summary generated successfully
[OK] Weekly report created!
```

### Custom Usage

**Generate report for different time ranges:**

```bash
# Last 14 days
uv run agent/weekly_report.py 14

# Last 30 days (monthly report)
uv run agent/weekly_report.py 30
```

**Schedule weekly reports (every Monday at 10 AM):**

```powershell
# Windows
schtasks /create /tn "JobSync-Weekly" /tr "uv run D:\Projects\JobSync\agent\weekly_report.py" /sc weekly /d MON /st 10:00
```

```bash
# Linux/Mac
crontab -e
# Add: 0 10 * * 1 cd /path/to/JobSync && uv run agent/weekly_report.py
```

### Troubleshooting Weekly Reports

**Error: "NOTION_WEEKLY_REPORTS_DB_ID not set"**

- Make sure `.env` file has `NOTION_WEEKLY_REPORTS_DB_ID=...`
- Database ID should be 32 characters (no dashes)
- Restart your terminal/IDE after updating `.env`

**Error: "No applications found in the past week"**

- Run the daily sync first: `uv run agent/main.py`
- Or manually add test applications to your Notion database
- Ensure applications have recent "Applied On" dates (within last 7 days)

**Error: "Failed to create weekly report"**

- Double-check property names in Notion (case-sensitive):
  - "Name" (Title type)
  - "Week Range" (Text type)
  - "Summary" (Text type)
  - "Created On" (Date type)
- Ensure database is shared with your integration
- Verify database ID in `.env` is correct

---

## ✅ Verify Your Setup

After setting up all components, test each one:

### 1. Test Gmail Authentication:

```bash
cd D:\Projects\JobSync
uv run python -c "from agent.gmail_client import list_messages; print('Gmail:', len(list_messages()), 'messages')"
```

Should show: `Gmail: [number] messages`

**First time:** Browser will open for OAuth → Grant permissions → Success!

**After first time:** Uses saved `token.json` (instant)

### 2. Test Notion Connection:

```bash
uv run agent/notion_utils.py
```

Should show: `[OK] Connected to Notion DB: [Your Database Name]`

### 3. Test LLM (optional):

```python
from agent.llm_utils import llm
print(llm.invoke("Hello!").content)
```

### 4. Test Full Agent:

```bash
uv run agent/main.py
```

Should show:

```
[EMAIL] Checking: [email subjects]...
[SKIP] Not a job application
[OK] Application found: [Company] - [Job Title]
...
[OK] Daily sync complete.
```

### 5. Test Weekly Report (Optional - requires Weekly Reports database):

```bash
uv run agent/weekly_report.py
```

Should show:

```
======================================================================
📊 WEEKLY JOB APPLICATION REPORT
======================================================================

[INFO] Generating report for: Oct 5 – Oct 12
[INFO] Fetching applications from Notion (last 7 days)...

[STATS] Weekly Statistics:
   Total Applications: 5
   📝 Applied: 3
   🎯 Interviews: 2
   ...

✅ [SUCCESS] Weekly report generated and saved to Notion!
```

**Note:** If you haven't set up the Weekly Reports database yet, see the "Weekly Report Agent Setup" section above.

---

## 🔒 Security Notes

### Environment Variables (.env)

- **Never commit `.env` to git** (it's in `.gitignore`)
- Keep your tokens secret (NOTION_TOKEN, OPENROUTER_KEY)
- Don't share screenshots with tokens visible
- Regenerate tokens if accidentally exposed

### Gmail OAuth Files

- ✅ `credentials.json` - Client ID/secret (safe to share with team, but keep private)
- ❌ `token.json` - YOUR personal Gmail access token (NEVER commit or share)
- ❌ `.env` - Contains API keys (NEVER commit)
- Both are automatically excluded via `.gitignore`

### What's Safe to Share

- ✅ Source code (`.py` files)
- ✅ Requirements and config files
- ❌ `.env` file
- ❌ `token.json`
- ❌ `credentials.json` (technically safe but keep private)

---

## ☁️ GitHub Actions Setup (Automation)

Automate daily syncs and weekly reports in GitHub without storing credentials in the repo.

### 1) Requirements (run locally once)

- Run: `uv run agent/main.py` to generate `agent/token.json`
- Ensure `.gitignore` excludes: `.env`, `agent/credentials.json`, `agent/token.json`

### 2) Add GitHub Secrets (paste raw values)

Settings → Secrets and variables → Actions → New repository secret

- `GMAIL_CREDENTIALS`: contents of `agent/credentials.json`
- `GMAIL_TOKEN`: contents of `agent/token.json`
- `NOTION_TOKEN`: from `.env`
- `NOTION_DATABASE_ID`: from `.env`
- `NOTION_WEEKLY_REPORTS_DB_ID`: from `.env`
- `OPENROUTER_KEY`: from `.env`
- Optional: `OPENROUTER_MODEL` (defaults to `anthropic/claude-3.5-sonnet`)

### 3) Workflows (already included)

Files:

- `.github/workflows/daily-sync.yml` (runs 09:00 UTC daily)
- `.github/workflows/weekly-report.yml` (runs Monday 10:00 UTC)

They reconstruct files at runtime:

```bash
mkdir -p agent
echo "$GMAIL_CREDENTIALS" > agent/credentials.json
echo "$GMAIL_TOKEN" > agent/token.json
```

And create `.env` from secrets for Notion/OpenRouter.

### 4) Permissions

Settings → Actions → General → Workflow permissions → Read and write

### 5) Optional overrides

You can change credential file locations using env vars:

- `GMAIL_CREDENTIALS_PATH`
- `GMAIL_TOKEN_PATH`

The default paths remain `agent/credentials.json` and `agent/token.json`.

### 6) Troubleshooting

- Secret not found → check secret names
- Invalid/expired token → re-run locally to regenerate `token.json`, update `GMAIL_TOKEN`
- Notion errors → verify DB sharing and property names
- Rate limits → add OpenRouter credits or use a cheaper model

## 🆘 Troubleshooting

### Environment Variables

**"NOTION_TOKEN not found"**

- Make sure `.env` file is in project root (same folder as `README.md`)
- No spaces around `=` in `.env`
- Token starts with `secret_`

**"NOTION_DATABASE_ID not found"**

- Copy the ID from Notion URL (32 characters, no dashes)
- Database must be shared with your integration
- Open database → Click `...` → Add connections → Select JobSync

**"OPENROUTER_KEY not found"**

- Key starts with `sk-or-v1-`
- Make sure you have credits in your OpenRouter account
- Go to https://openrouter.ai/ → Credits → Add funds

### Gmail OAuth Issues

**"credentials.json not found"**

1. Download OAuth credentials from Google Cloud Console
2. Rename to `credentials.json` (exactly)
3. Place in `agent/` folder (not root folder)

**"Error 403: access_denied"**

- Your Gmail account is NOT added as a test user
- Go to Google Cloud Console → OAuth consent screen → Test users → Add your email
- Must use EXACT email address you're trying to authenticate with

**"redirect_uri_mismatch"**

- You created a "Web application" instead of "Desktop app"
- Delete the credential and create a new one as **Desktop app**
- Desktop apps automatically support `http://localhost`

**"Port already in use" / "[WinError 10013]"**

- The code tries multiple ports automatically (8080, 49256, 8000)
- If all fail, it falls back to manual authentication
- Copy the URL, paste in browser, copy the code back

**"Browser doesn't open" on first run**

- Copy the URL from console and paste in your browser manually
- Complete OAuth flow
- `token.json` will be created

**"The authentication flow has completed" but still fails**

- Check if `token.json` was created in `agent/` folder
- If not, you may need to run as administrator
- Or manually copy the auth code from the URL

### General Issues

**"Module not found" errors**

- Run `uv sync` to install dependencies
- Make sure you're in the project directory

**"No module named 'dotenv'"**

- Run `uv sync` or `pip install python-dotenv`

**Rate limit errors from OpenRouter**

- The code automatically retries with 10s, 20s, 30s delays
- If it persists, add more credits to your OpenRouter account
- Or wait a few minutes and try again

---

## 📚 References

### API Documentation

- [Gmail API - Python Quickstart](https://developers.google.com/gmail/api/quickstart/python)
- [Gmail API - OAuth 2.0](https://developers.google.com/identity/protocols/oauth2)
- [Notion API - Getting Started](https://developers.notion.com/docs/getting-started)
- [OpenRouter Documentation](https://openrouter.ai/docs)

### OAuth Setup Guides

- [Google Cloud Console](https://console.cloud.google.com/)
- [OAuth 2.0 for Desktop Apps](https://developers.google.com/identity/protocols/oauth2/native-app)
- [Understanding OAuth 2.0](https://developers.google.com/identity/protocols/oauth2)

### Best Practices

- [Environment Variables Best Practices](https://12factor.net/config)
- [Securing API Keys](https://cloud.google.com/docs/authentication/api-keys)
