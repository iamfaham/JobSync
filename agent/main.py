import asyncio
import sys
import os

# Add parent directory to path to import from workflows
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from workflows.job_sync_workflow import JobSyncWorkflow


async def daily_sync():
    """Main entry point for JobSync using MCP + LangGraph workflow"""
    print("Starting JobSyncd with MCP + LangGraph...")

    workflow = JobSyncWorkflow()
    result = await workflow.run()

    if isinstance(result, dict) and "processed_emails" in result:
        print(f"Processed {len(result['processed_emails'])} applications")
        if result.get("errors"):
            print(f"Errors: {result['errors']}")
    else:
        print(f"Result: {result}")

    return result


if __name__ == "__main__":
    asyncio.run(daily_sync())
