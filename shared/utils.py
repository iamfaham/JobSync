"""
Shared utility functions for JobSync application.
Consolidates common formatting and helper functions.
"""

import os
import sys
from typing import List, Dict, Any
from datetime import datetime, timedelta


def setup_path_imports():
    """Setup path imports for parent directory access."""
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def format_entries_for_llm(entries: List[Dict[str, str]]) -> str:
    """Format entries for LLM processing."""
    if not entries:
        return "No recent applications found."

    entries_text = ""
    for i, entry in enumerate(entries[:10], 1):  # Limit to 10 entries
        entries_text += f"{i}. **{entry.get('company', 'Unknown')}** - {entry.get('job_title', 'Unknown')}\n"
        entries_text += f"   Status: {entry.get('status', 'Applied')} | Applied: {entry.get('applied_on', 'Unknown')}\n"
        if entry.get("notes"):
            entries_text += f"   Notes: {entry.get('notes', '')[:100]}...\n"
        entries_text += "\n"

    return entries_text


def format_deadlines_for_llm(deadlines: List[Dict[str, str]]) -> str:
    """Format deadlines for LLM processing."""
    if not deadlines:
        return "No upcoming deadlines found."

    deadlines_text = ""
    for i, deadline in enumerate(deadlines, 1):
        deadlines_text += f"{i}. **{deadline.get('company', 'Unknown')}** - {deadline.get('job_title', 'Unknown')}\n"
        deadlines_text += f"   Note: {deadline.get('note', '')[:200]}...\n\n"

    return deadlines_text


def generate_week_range(days: int) -> str:
    """Generate week range string for reports."""
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=days - 1)
    return f"{start_date.strftime('%b %d')} – {end_date.strftime('%b %d')}"


def get_llm_config():
    """Get standardized LLM configuration."""
    from langchain_openai import ChatOpenAI

    return ChatOpenAI(
        model=os.getenv(
            "OPENROUTER_MODEL", "mistralai/mistral-small-3.2-24b-instruct:free"
        ),
        base_url="https://openrouter.ai/api/v1",
        api_key=os.getenv("OPENROUTER_KEY"),
        temperature=0,
    )


def get_llm_config_creative():
    """Get LLM configuration with slightly higher temperature for creative tasks."""
    from langchain_openai import ChatOpenAI

    return ChatOpenAI(
        model=os.getenv(
            "OPENROUTER_MODEL", "mistralai/mistral-small-3.2-24b-instruct:free"
        ),
        base_url="https://openrouter.ai/api/v1",
        api_key=os.getenv("OPENROUTER_KEY"),
        temperature=0.3,  # Slightly more creative for summaries
    )
