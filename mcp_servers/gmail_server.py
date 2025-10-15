import asyncio
from typing import List, Optional
from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
from pydantic import BaseModel
import sys
import os

# Add parent directory to path to import existing Gmail client
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from agent.gmail_client import list_messages, get_message, message_summary


class EmailData(BaseModel):
    id: str
    subject: str
    sender: str
    date: str
    text: str
    snippet: str


class GmailMCPServer:
    def __init__(self):
        self.server = Server("gmail-mcp-server")
        self._setup_tools()

    def _setup_tools(self):
        @self.server.list_tools()
        async def list_tools() -> List[Tool]:
            return [
                Tool(
                    name="get_recent_emails",
                    description="Fetch recent emails from Gmail",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "max_results": {
                                "type": "integer",
                                "description": "Maximum number of emails to fetch",
                                "default": 10,
                            },
                            "newer_than_days": {
                                "type": "integer",
                                "description": "Only fetch emails newer than X days",
                                "default": 7,
                            },
                        },
                    },
                ),
                Tool(
                    name="get_email_content",
                    description="Get full content of a specific email",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "email_id": {
                                "type": "string",
                                "description": "Gmail message ID",
                            }
                        },
                        "required": ["email_id"],
                    },
                ),
                Tool(
                    name="mark_email_processed",
                    description="Mark an email as processed",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "email_id": {
                                "type": "string",
                                "description": "Gmail message ID to mark as processed",
                            }
                        },
                        "required": ["email_id"],
                    },
                ),
            ]

        @self.server.call_tool()
        async def call_tool(name: str, arguments: dict) -> List[TextContent]:
            if name == "get_recent_emails":
                max_results = arguments.get("max_results", 10)
                newer_than_days = arguments.get("newer_than_days", 7)

                try:
                    msg_ids = list_messages(
                        max_results=max_results, newer_than_days=newer_than_days
                    )
                    emails = []

                    for msg_id in msg_ids:
                        msg = get_message(msg_id["id"])
                        summary = message_summary(msg)
                        emails.append(
                            EmailData(
                                id=summary["id"],
                                subject=summary.get("subject", ""),
                                sender=summary.get("from", ""),
                                date=summary.get("date", ""),
                                text=summary.get("text", ""),
                                snippet=summary.get("snippet", ""),
                            )
                        )

                    return [
                        TextContent(type="text", text=f"Fetched {len(emails)} emails")
                    ]

                except Exception as e:
                    return [
                        TextContent(
                            type="text", text=f"Error fetching emails: {str(e)}"
                        )
                    ]

            elif name == "get_email_content":
                email_id = arguments["email_id"]
                try:
                    msg = get_message(email_id)
                    summary = message_summary(msg)
                    return [
                        TextContent(
                            type="text",
                            text=f"Email content: {summary['text'][:1000]}...",
                        )
                    ]
                except Exception as e:
                    return [
                        TextContent(
                            type="text", text=f"Error fetching email content: {str(e)}"
                        )
                    ]

            elif name == "mark_email_processed":
                email_id = arguments["email_id"]
                # In a real implementation, you'd save this to a database
                return [
                    TextContent(
                        type="text", text=f"Marked email {email_id} as processed"
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
                    server_name="gmail-mcp-server",
                    server_version="1.0.0",
                    capabilities=self.server.get_capabilities(
                        notification_options=None, experimental_capabilities=None
                    ),
                ),
            )


if __name__ == "__main__":
    server = GmailMCPServer()
    asyncio.run(server.run())
