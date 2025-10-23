import asyncio
import json
from typing import List, Optional
from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
import sys
import os

# Add parent directory to path to import existing Notion client
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from agent.notion_utils import (
    create_or_update_entry,
    find_entry_by_app_id,
    create_weekly_report,
    notion,
    NOTION_DATABASE_ID,
)
from shared.models import JobApplicationData


class NotionMCPServer:
    def __init__(self):
        self.server = Server("notion-mcp-server")
        self._setup_tools()

    def _setup_tools(self):
        @self.server.list_tools()
        async def list_tools() -> List[Tool]:
            return [
                Tool(
                    name="create_job_application",
                    description="Create a new job application entry in Notion",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "company": {"type": "string"},
                            "job_title": {"type": "string"},
                            "status": {"type": "string"},
                            "applied_on": {"type": "string"},
                            "notes": {"type": "string", "default": ""},
                            "app_id": {"type": "string", "default": None},
                        },
                        "required": ["company", "job_title", "status", "applied_on"],
                    },
                ),
                Tool(
                    name="update_job_application",
                    description="Update an existing job application",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "app_id": {"type": "string"},
                            "updates": {"type": "object"},
                        },
                        "required": ["app_id", "updates"],
                    },
                ),
                Tool(
                    name="find_application_by_id",
                    description="Find application by ID to check for duplicates",
                    inputSchema={
                        "type": "object",
                        "properties": {"app_id": {"type": "string"}},
                        "required": ["app_id"],
                    },
                ),
                Tool(
                    name="create_weekly_report",
                    description="Create weekly report entry",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "title": {"type": "string"},
                            "week_range": {"type": "string"},
                            "summary": {"type": "string"},
                            "created_on": {"type": "string"},
                        },
                        "required": ["title", "week_range", "summary", "created_on"],
                    },
                ),
                Tool(
                    name="search_similar_entries",
                    description="Search for similar job application entries in the database",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "company": {
                                "type": "string",
                                "description": "Company name to search for",
                            },
                            "job_title": {
                                "type": "string",
                                "description": "Job title to search for",
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Maximum number of results to return",
                                "default": 10,
                            },
                        },
                        "required": ["company", "job_title"],
                    },
                ),
                Tool(
                    name="update_existing_entry",
                    description="Update an existing job application entry",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "entry_id": {
                                "type": "string",
                                "description": "Notion page ID of the entry to update",
                            },
                            "status": {
                                "type": "string",
                                "description": "New status for the entry",
                            },
                            "notes": {
                                "type": "string",
                                "description": "Additional notes to append",
                                "default": "",
                            },
                        },
                        "required": ["entry_id", "status"],
                    },
                ),
                Tool(
                    name="get_all_recent_entries",
                    description="Get all recent job application entries for duplicate detection",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "days": {
                                "type": "integer",
                                "description": "Number of days to look back",
                                "default": 30,
                            }
                        },
                    },
                ),
            ]

        @self.server.call_tool()
        async def call_tool(name: str, arguments: dict) -> List[TextContent]:
            if name == "create_job_application":
                try:
                    result, was_updated = create_or_update_entry(
                        company=arguments["company"],
                        job_title=arguments["job_title"],
                        status=arguments["status"],
                        applied_on=arguments["applied_on"],
                        notes=arguments.get("notes", ""),
                        app_id=arguments.get("app_id"),
                    )

                    if result:
                        action = "Updated" if was_updated else "Created"
                        return [
                            TextContent(
                                type="text",
                                text=f"{action} job application: {arguments['company']} - {arguments['job_title']}",
                            )
                        ]
                    else:
                        return [
                            TextContent(
                                type="text",
                                text="Failed to create/update job application",
                            )
                        ]

                except Exception as e:
                    return [
                        TextContent(
                            type="text",
                            text=f"Error creating job application: {str(e)}",
                        )
                    ]

            elif name == "find_application_by_id":
                app_id = arguments["app_id"]
                try:
                    existing = find_entry_by_app_id(app_id)
                    if existing:
                        return [
                            TextContent(
                                type="text",
                                text=f"Found existing application with ID: {app_id}",
                            )
                        ]
                    else:
                        return [
                            TextContent(
                                type="text",
                                text=f"No existing application found with ID: {app_id}",
                            )
                        ]
                except Exception as e:
                    return [
                        TextContent(
                            type="text", text=f"Error finding application: {str(e)}"
                        )
                    ]

            elif name == "create_weekly_report":
                try:
                    result = create_weekly_report(
                        title=arguments["title"],
                        week_range=arguments["week_range"],
                        summary=arguments["summary"],
                        created_on=arguments["created_on"],
                    )

                    if result:
                        return [
                            TextContent(
                                type="text",
                                text=f"Created weekly report: {arguments['title']}",
                            )
                        ]
                    else:
                        return [
                            TextContent(
                                type="text", text="Failed to create weekly report"
                            )
                        ]

                except Exception as e:
                    return [
                        TextContent(
                            type="text", text=f"Error creating weekly report: {str(e)}"
                        )
                    ]

            elif name == "search_similar_entries":
                company = arguments["company"]
                job_title = arguments["job_title"]
                limit = arguments.get("limit", 10)

                try:
                    # Search for entries with similar company name
                    resp = notion.databases.query(
                        database_id=NOTION_DATABASE_ID,
                        filter={
                            "property": "Company",
                            "rich_text": {"contains": company},
                        },
                        page_size=limit,
                    )

                    # Format results for LLM
                    entries = []
                    for page in resp.get("results", []):
                        props = page.get("properties", {})
                        entries.append(
                            {
                                "id": page["id"],
                                "company": props.get("Company", {})
                                .get("rich_text", [{}])[0]
                                .get("text", {})
                                .get("content", ""),
                                "job_title": props.get("Job Title", {})
                                .get("rich_text", [{}])[0]
                                .get("text", {})
                                .get("content", ""),
                                "status": props.get("Status", {})
                                .get("status", {})
                                .get("name", ""),
                                "applied_on": props.get("Applied On", {})
                                .get("date", {})
                                .get("start", ""),
                                "notes": props.get("Notes", {})
                                .get("rich_text", [{}])[0]
                                .get("text", {})
                                .get("content", ""),
                                "app_id": props.get("Application ID", {})
                                .get("rich_text", [{}])[0]
                                .get("text", {})
                                .get("content", ""),
                            }
                        )

                    return [TextContent(type="text", text=json.dumps(entries))]

                except Exception as e:
                    return [
                        TextContent(
                            type="text", text=f"Error searching entries: {str(e)}"
                        )
                    ]

            elif name == "update_existing_entry":
                entry_id = arguments["entry_id"]
                status = arguments["status"]
                notes = arguments.get("notes", "")

                try:
                    # Update the existing entry
                    update_props = {"Status": {"status": {"name": status}}}

                    if notes:
                        # Get existing notes and append new ones
                        existing_page = notion.pages.retrieve(page_id=entry_id)
                        existing_notes = (
                            existing_page.get("properties", {})
                            .get("Notes", {})
                            .get("rich_text", [])
                        )
                        old_notes_text = (
                            existing_notes[0].get("text", {}).get("content", "")
                            if existing_notes
                            else ""
                        )
                        new_notes = f"{old_notes_text}\n\n[Update] {notes}".strip()
                        update_props["Notes"] = {
                            "rich_text": [{"text": {"content": new_notes}}]
                        }

                    result = notion.pages.update(
                        page_id=entry_id, properties=update_props
                    )

                    return [
                        TextContent(
                            type="text",
                            text=f"Updated entry {entry_id} with status: {status}",
                        )
                    ]

                except Exception as e:
                    return [
                        TextContent(type="text", text=f"Error updating entry: {str(e)}")
                    ]

            elif name == "get_all_recent_entries":
                days = arguments.get("days", 30)

                # Convert days to integer if it's a string (common when called by LLM)
                if isinstance(days, str):
                    days = int(days)

                try:
                    # Get all recent entries
                    resp = notion.databases.query(
                        database_id=NOTION_DATABASE_ID,
                        page_size=100,  # Adjust based on your needs
                    )

                    # Format results for LLM
                    entries = []
                    for page in resp.get("results", []):
                        props = page.get("properties", {})
                        entries.append(
                            {
                                "id": page["id"],
                                "company": props.get("Company", {})
                                .get("rich_text", [{}])[0]
                                .get("text", {})
                                .get("content", ""),
                                "job_title": props.get("Job Title", {})
                                .get("rich_text", [{}])[0]
                                .get("text", {})
                                .get("content", ""),
                                "status": props.get("Status", {})
                                .get("status", {})
                                .get("name", ""),
                                "applied_on": props.get("Applied On", {})
                                .get("date", {})
                                .get("start", ""),
                                "notes": props.get("Notes", {})
                                .get("rich_text", [{}])[0]
                                .get("text", {})
                                .get("content", ""),
                                "app_id": props.get("Application ID", {})
                                .get("rich_text", [{}])[0]
                                .get("text", {})
                                .get("content", ""),
                            }
                        )

                    return [TextContent(type="text", text=json.dumps(entries))]

                except Exception as e:
                    return [
                        TextContent(
                            type="text", text=f"Error getting recent entries: {str(e)}"
                        )
                    ]

            else:
                return [TextContent(type="text", text=f"Unknown tool: {name}")]

    async def run(self):
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="notion-mcp-server",
                    server_version="1.0.0",
                    capabilities=self.server.get_capabilities(
                        notification_options=None, experimental_capabilities=None
                    ),
                ),
            )


if __name__ == "__main__":
    server = NotionMCPServer()
    asyncio.run(server.run())
