"""
Shared entry point utilities for JobSync application.
Consolidates common entry point logic and error handling.
"""

import asyncio
import sys
import os
from typing import Any, Dict, Optional


def setup_entry_point():
    """Setup common entry point configuration."""
    # Add parent directory to path to import from workflows
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


async def run_workflow_with_error_handling(
    workflow_func, *args, **kwargs
) -> Optional[Dict[str, Any]]:
    """Run a workflow function with standardized error handling."""
    try:
        result = await workflow_func(*args, **kwargs)

        if isinstance(result, dict):
            if "processed_emails" in result:
                print(f"Processed {len(result['processed_emails'])} applications")
            if result.get("errors"):
                print(f"Errors: {result['errors']}")
        else:
            print(f"Result: {result}")

        return result

    except Exception as e:
        print(f"Error: {e}")
        import traceback

        traceback.print_exc()
        return None


def run_weekly_report_with_error_handling(
    workflow_func, days: int
) -> Optional[Dict[str, Any]]:
    """Run weekly report workflow with standardized error handling."""
    try:
        result = asyncio.run(workflow_func(days))

        if result and result.get("summary"):
            print(f"✅ Weekly report generated successfully!")
            print(f"📅 Week Range: {result.get('week_range', 'Unknown')}")
        else:
            print(f"❌ Failed to generate weekly report")
            if result and result.get("errors"):
                print(f"Errors: {result['errors']}")

        return result

    except Exception as e:
        print(f"Error: {e}")
        import traceback

        traceback.print_exc()
        return None
