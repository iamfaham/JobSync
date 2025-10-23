import asyncio
import sys
import os

# Add parent directory to path to import from workflows
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from workflows.job_sync_workflow import JobSyncWorkflow
from shared.entry_points import run_workflow_with_error_handling


async def daily_sync():
    """Main entry point for JobSync using MCP + LangGraph workflow"""
    print("Starting JobSyncd with MCP + LangGraph...")

    workflow = JobSyncWorkflow()
    return await run_workflow_with_error_handling(workflow.run)


if __name__ == "__main__":
    asyncio.run(daily_sync())
