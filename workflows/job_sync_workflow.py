from typing import TypedDict, List, Optional, Dict, Any
from langchain.tools import Tool
from langchain.agents import initialize_agent, AgentType
import os
import sys
import json
import asyncio
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Import shared modules
from shared.models import EmailData, JobApplicationData
from shared.utils import get_llm_config
from shared.config import validate_config

# Validate configuration
validate_config()


class JobSyncWorkflow:
    def __init__(self):
        # Initialize LLM with shared configuration
        self.llm = get_llm_config()

        # Create MCP tools for LLM
        self.tools = self._create_mcp_tools()

        # Create agent with tools
        self.agent = self._create_agent()

    def _create_mcp_tools(self) -> List[Tool]:
        """Create LangChain tools that wrap MCP calls"""
        return [
            Tool(
                name="get_recent_emails",
                description="Fetch recent job application emails from Gmail. Use this to get new emails to process.",
                func=self._call_gmail_mcp,
            ),
            Tool(
                name="search_similar_entries",
                description="Search for similar job application entries in Notion database. Use this to check for duplicates before creating new entries.",
                func=self._call_notion_search,
            ),
            Tool(
                name="create_job_application",
                description="Create a new job application entry in Notion. Use this for new applications that don't have duplicates.",
                func=self._call_notion_create,
            ),
            Tool(
                name="update_existing_entry",
                description="Update an existing job application entry with new status or notes. Use this when you find a duplicate that needs updating.",
                func=self._call_notion_update,
            ),
            Tool(
                name="get_all_recent_entries",
                description="Get all recent job application entries from the database. Use this to get an overview of existing entries.",
                func=self._call_notion_get_all,
            ),
        ]

    def _create_agent(self):
        """Create the LLM agent with tools"""
        return initialize_agent(
            tools=self.tools,
            llm=self.llm,
            agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
            verbose=True,
            handle_parsing_errors=True,
        )

    def _call_gmail_mcp(self, query: str = "") -> str:
        """Call Gmail MCP to get recent emails"""
        try:
            from agent.gmail_client import list_messages, get_message, message_summary

            # Filter for job application related emails only
            gmail_query = "application OR applied OR interview OR assessment OR offer OR rejection -label:spam -label:promotions"
            msg_ids = list_messages(
                query=gmail_query, max_results=10, newer_than_days=7
            )

            emails = []
            for msg_id in msg_ids:
                msg = get_message(msg_id["id"])
                summary = message_summary(msg)
                emails.append(
                    {
                        "id": summary["id"],
                        "subject": summary.get("subject", ""),
                        "sender": summary.get("from", ""),
                        "date": summary.get("date", ""),
                        "text": summary.get("text", ""),
                        "snippet": summary.get("snippet", ""),
                    }
                )

            return f"Retrieved {len(emails)} emails from Gmail:\n" + json.dumps(
                emails, indent=2
            )

        except Exception as e:
            return f"Error fetching emails: {str(e)}"

    def _call_notion_search(self, company: str = "", job_title: str = "") -> str:
        """Call Notion MCP to search for similar entries"""
        try:
            from agent.notion_utils import find_entry_by_company_title

            # Search for existing entry
            existing = find_entry_by_company_title(company, job_title)

            if existing:
                props = existing.get("properties", {})
                return f"Found existing entry: {company} - {job_title} (ID: {existing['id']})"
            else:
                return f"No existing entry found for {company} - {job_title}"

        except Exception as e:
            return f"Error searching entries: {str(e)}"

    def _call_notion_create(
        self,
        company: str = "",
        job_title: str = "",
        status: str = "",
        applied_on: str = "",
        notes: str = "",
        app_id: str = "",
    ) -> str:
        """Call Notion MCP to create new entry"""
        try:
            from agent.notion_utils import create_or_update_entry

            result, was_updated = create_or_update_entry(
                company=company,
                job_title=job_title,
                status=status,
                applied_on=applied_on,
                notes=notes,
                app_id=app_id,
            )

            if result:
                action = "Updated" if was_updated else "Created"
                return f"{action} job application: {company} - {job_title}"
            else:
                return (
                    f"Failed to create/update job application: {company} - {job_title}"
                )

        except Exception as e:
            return f"Error creating job application: {str(e)}"

    def _call_notion_update(
        self, entry_id: str = "", status: str = "", notes: str = ""
    ) -> str:
        """Call Notion MCP to update existing entry"""
        try:
            from agent.notion_utils import update_entry

            result = update_entry(entry_id, status)

            if result:
                return f"Updated entry {entry_id} with status: {status}"
            else:
                return f"Failed to update entry {entry_id}"

        except Exception as e:
            return f"Error updating entry: {str(e)}"

    def _call_notion_get_all(self, days: int = 30) -> str:
        """Call Notion MCP to get all recent entries"""
        try:
            from agent.notion_utils import query_recent_entries

            entries = query_recent_entries(days)
            return (
                f"Retrieved {len(entries)} recent entries from database:\n"
                + json.dumps(entries, indent=2)
            )

        except Exception as e:
            return f"Error getting recent entries: {str(e)}"

    async def run(self):
        """Run the LLM agent with direct tool access"""
        print("Starting JobSync with LLM + MCP tools...")

        try:
            # Let the LLM agent handle everything
            result = self.agent.run(
                "Process recent job application emails and manage duplicates in the Notion database"
            )

            print("\nLLM agent completed processing!")
            print(f"Result: {result}")
            return result

        except Exception as e:
            print(f"Error: {e}")
            import traceback

            traceback.print_exc()
            return None


# Usage
async def main():
    workflow = JobSyncWorkflow()
    result = await workflow.run()
    return result


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
