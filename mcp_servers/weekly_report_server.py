"""
MCP Server for Weekly Report functionality
Provides tools for generating weekly reports and summaries
"""

from mcp.server import Server
from mcp.types import Tool, TextContent
from typing import List, Dict, Any, Optional
import json
import os
import sys
from datetime import datetime, timedelta

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from agent.notion_utils import get_weekly_application_data, create_weekly_report


# Initialize MCP server
server = Server("weekly-report-server")


@server.list_tools()
async def list_tools() -> List[Tool]:
    """List available tools for weekly report operations"""
    return [
        Tool(
            name="get_weekly_data",
            description="Fetch weekly application data from Notion database",
            inputSchema={
                "type": "object",
                "properties": {
                    "days": {
                        "type": "integer",
                        "description": "Number of days to look back (default: 7)",
                        "default": 7
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="create_weekly_report",
            description="Create a weekly report entry in Notion",
            inputSchema={
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "Report title"
                    },
                    "week_range": {
                        "type": "string",
                        "description": "Week range text"
                    },
                    "summary": {
                        "type": "string",
                        "description": "AI-generated summary content"
                    },
                    "created_on": {
                        "type": "string",
                        "description": "Creation date in YYYY-MM-DD format"
                    }
                },
                "required": ["title", "week_range", "summary", "created_on"]
            }
        ),
        Tool(
            name="format_entries_for_llm",
            description="Format application entries for LLM processing",
            inputSchema={
                "type": "object",
                "properties": {
                    "entries": {
                        "type": "array",
                        "description": "List of application entries",
                        "items": {
                            "type": "object",
                            "properties": {
                                "company": {"type": "string"},
                                "job_title": {"type": "string"},
                                "status": {"type": "string"},
                                "applied_on": {"type": "string"},
                                "notes": {"type": "string"}
                            }
                        }
                    }
                },
                "required": ["entries"]
            }
        ),
        Tool(
            name="format_deadlines_for_llm",
            description="Format deadlines for LLM processing",
            inputSchema={
                "type": "object",
                "properties": {
                    "deadlines": {
                        "type": "array",
                        "description": "List of deadline entries",
                        "items": {
                            "type": "object",
                            "properties": {
                                "company": {"type": "string"},
                                "job_title": {"type": "string"},
                                "note": {"type": "string"}
                        }
                    }
                },
                "required": ["deadlines"]
            }
        )
    ]


@server.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle tool calls for weekly report operations"""
    
    if name == "get_weekly_data":
        days = arguments.get("days", 7)
        try:
            data = get_weekly_application_data(days)
            if data:
                return [TextContent(
                    type="text",
                    text=f"Weekly data retrieved successfully:\n{json.dumps(data, indent=2)}"
                )]
            else:
                return [TextContent(
                    type="text",
                    text="Failed to retrieve weekly data from Notion"
                )]
        except Exception as e:
            return [TextContent(
                type="text",
                text=f"Error retrieving weekly data: {str(e)}"
            )]
    
    elif name == "create_weekly_report":
        title = arguments.get("title")
        week_range = arguments.get("week_range")
        summary = arguments.get("summary")
        created_on = arguments.get("created_on")
        
        try:
            result = create_weekly_report(title, week_range, summary, created_on)
            if result:
                return [TextContent(
                    type="text",
                    text=f"Weekly report created successfully: {result.get('id', 'Unknown')[:8]}..."
                )]
            else:
                return [TextContent(
                    type="text",
                    text="Failed to create weekly report in Notion"
                )]
        except Exception as e:
            return [TextContent(
                type="text",
                text=f"Error creating weekly report: {str(e)}"
            )]
    
    elif name == "format_entries_for_llm":
        entries = arguments.get("entries", [])
        try:
            formatted_text = _format_entries_for_llm(entries)
            return [TextContent(
                type="text",
                text=formatted_text
            )]
        except Exception as e:
            return [TextContent(
                type="text",
                text=f"Error formatting entries: {str(e)}"
            )]
    
    elif name == "format_deadlines_for_llm":
        deadlines = arguments.get("deadlines", [])
        try:
            formatted_text = _format_deadlines_for_llm(deadlines)
            return [TextContent(
                type="text",
                text=formatted_text
            )]
        except Exception as e:
            return [TextContent(
                type="text",
                text=f"Error formatting deadlines: {str(e)}"
            )]
    
    else:
        return [TextContent(
            type="text",
            text=f"Unknown tool: {name}"
        )]


def _format_entries_for_llm(entries: List[Dict[str, str]]) -> str:
    """Format entries for LLM processing"""
    if not entries:
        return "No recent applications found."
    
    entries_text = ""
    for i, entry in enumerate(entries[:10], 1):  # Limit to 10 entries
        entries_text += f"{i}. **{entry.get('company', 'Unknown')}** - {entry.get('job_title', 'Unknown')}\n"
        entries_text += f"   Status: {entry.get('status', 'Applied')} | Applied: {entry.get('applied_on', 'Unknown')}\n"
        if entry.get('notes'):
            entries_text += f"   Notes: {entry.get('notes', '')[:100]}...\n"
        entries_text += "\n"
    
    return entries_text


def _format_deadlines_for_llm(deadlines: List[Dict[str, str]]) -> str:
    """Format deadlines for LLM processing"""
    if not deadlines:
        return "No upcoming deadlines found."
    
    deadlines_text = ""
    for i, deadline in enumerate(deadlines, 1):
        deadlines_text += f"{i}. **{deadline.get('company', 'Unknown')}** - {deadline.get('job_title', 'Unknown')}\n"
        deadlines_text += f"   Note: {deadline.get('note', '')[:200]}...\n\n"
    
    return deadlines_text


# Run the server
if __name__ == "__main__":
    import asyncio
    asyncio.run(server.run())
