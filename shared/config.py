"""
Shared configuration and environment setup for JobSync application.
Consolidates environment variable loading and configuration.
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Environment variables
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID")
NOTION_WEEKLY_REPORTS_DB_ID = os.getenv("NOTION_WEEKLY_REPORTS_DB_ID")
OPENROUTER_KEY = os.getenv("OPENROUTER_KEY")
OPENROUTER_MODEL = os.getenv(
    "OPENROUTER_MODEL", "mistralai/mistral-small-3.2-24b-instruct:free"
)

# Gmail configuration
GMAIL_CREDENTIALS_PATH = os.getenv("GMAIL_CREDENTIALS_PATH")
GMAIL_TOKEN_PATH = os.getenv("GMAIL_TOKEN_PATH")


def validate_config():
    """Validate that all required environment variables are set."""
    required_vars = ["NOTION_TOKEN", "NOTION_DATABASE_ID", "OPENROUTER_KEY"]

    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)

    if missing_vars:
        raise ValueError(
            f"Missing required environment variables: {', '.join(missing_vars)}"
        )

    return True
