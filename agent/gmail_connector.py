import os
import sys
from dotenv import load_dotenv

# Add parent directory to path to import from gmail_mcp
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from gmail_mcp.gmail_client import list_messages, get_message, message_summary

load_dotenv()

def get_recent_emails(max_results=10, newer_than_days=7):
    """
    Fetch recent emails and return them as a list of dicts with parsed content.
    """
    try:
        # Get message IDs
        msg_ids = list_messages(max_results=max_results, newer_than_days=newer_than_days)
        
        # Fetch and parse each message
        emails = []
        for msg_id in msg_ids:
            msg = get_message(msg_id["id"])
            summary = message_summary(msg)
            emails.append(summary)
        
        return emails
    except Exception as e:
        print(f"❌ Error fetching emails: {e}")
        return []
