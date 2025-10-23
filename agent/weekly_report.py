import asyncio
import sys
import os

# Add parent directory to path to import from workflows
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from workflows.weekly_report_workflow import WeeklyReportWorkflow
from shared.entry_points import run_weekly_report_with_error_handling


async def main():
    """Main entry point for Weekly Report using MCP + LangGraph workflow"""
    import sys

    # Get days from command line argument
    days = 7
    if len(sys.argv) > 1:
        try:
            days = int(sys.argv[1])
        except ValueError:
            print("Invalid days argument, using default 7 days")

    print(f"🚀 Starting Weekly Report with MCP + LangGraph for {days} days...")

    workflow = WeeklyReportWorkflow()
    return await run_weekly_report_with_error_handling(workflow.run, days)


if __name__ == "__main__":
    asyncio.run(main())
