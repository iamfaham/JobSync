import asyncio
from typing import List, Optional
from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
from pydantic import BaseModel
import sys
import os

# Add parent directory to path to import existing Notion client
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from agent.notion_utils import (
    create_or_update_entry,
    find_entry_by_app_id,
    create_weekly_report,
)


class JobApplicationData(BaseModel):
    company: str
    job_title: str
    status: str
    applied_on: str
    notes: str = ""
    app_id: Optional[str] = None


class WeeklyReportData(BaseModel):
    title: str
    week_range: str
    summary: str
    created_on: str


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
