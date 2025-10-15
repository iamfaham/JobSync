import asyncio
import sys
import os

# Add parent directory to path to import from workflows
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from workflows.job_sync_workflow import JobSyncWorkflow


async def daily_sync():
    """Main entry point for JobSync using MCP + LangGraph workflow"""
    print("🚀 Starting JobSync with MCP + LangGraph...")

    workflow = JobSyncWorkflow()
    result = await workflow.run()

    print(f"✅ Processed {len(result['processed_emails'])} applications")
    if result["errors"]:
        print(f"❌ Errors: {result['errors']}")

    return result


if __name__ == "__main__":
    asyncio.run(daily_sync())
