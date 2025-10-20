from typing import TypedDict, List, Optional, Dict, Any
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from pydantic import BaseModel
import os
import sys
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

load_dotenv()


class WeeklyReportData(BaseModel):
    total: int
    applied: int
    interview: int
    assessment: int
    offer: int
    rejected: int
    deadlines: List[Dict[str, str]]
    entries: List[Dict[str, str]]


class WeeklyReportState(TypedDict):
    days: int
    report_data: Optional[WeeklyReportData]
    summary: Optional[str]
    week_range: Optional[str]
    errors: List[str]


class WeeklyReportWorkflow:
    def __init__(self):
        # Initialize LLM with OpenRouter
        self.llm = ChatOpenAI(
            model=os.getenv(
                "OPENROUTER_MODEL", "mistralai/mistral-small-3.2-24b-instruct:free"
            ),
            base_url="https://openrouter.ai/api/v1",
            api_key=os.getenv("OPENROUTER_KEY"),
            temperature=0.3,  # Slightly more creative for summaries
        )

        # Create the workflow graph
        self.workflow = self._create_workflow()

    def _create_workflow(self) -> StateGraph:
        workflow = StateGraph(WeeklyReportState)

        # Add nodes
        workflow.add_node("fetch_data", self._fetch_data_node)
        workflow.add_node("generate_summary", self._generate_summary_node)
        workflow.add_node("create_report", self._create_report_node)

        # Set entry point
        workflow.set_entry_point("fetch_data")

        # Add edges
        workflow.add_edge("fetch_data", "generate_summary")
        workflow.add_edge("generate_summary", "create_report")
        workflow.add_edge("create_report", END)

        return workflow.compile()

    async def _fetch_data_node(self, state: WeeklyReportState) -> WeeklyReportState:
        """Fetch weekly application data from Notion"""
        from agent.notion_utils import get_weekly_application_data

        try:
            days = state.get("days", 7)
            print(f"[FETCH] Fetching data for the last {days} days...")

            # Get weekly data from Notion
            data = get_weekly_application_data(days)

            if not data:
                print("[ERROR] Failed to fetch weekly data from Notion")
                return {**state, "errors": ["Failed to fetch weekly data from Notion"]}

            # Convert to WeeklyReportData
            report_data = WeeklyReportData(
                total=data.get("total", 0),
                applied=data.get("applied", 0),
                interview=data.get("interview", 0),
                assessment=data.get("assessment", 0),
                offer=data.get("offer", 0),
                rejected=data.get("rejected", 0),
                deadlines=data.get("deadlines", []),
                entries=data.get("entries", []),
            )

            print(f"[FETCH] Retrieved {report_data.total} total applications")
            print(f"  - Applied: {report_data.applied}")
            print(f"  - Interviews: {report_data.interview}")
            print(f"  - Assessments: {report_data.assessment}")
            print(f"  - Offers: {report_data.offer}")
            print(f"  - Rejected: {report_data.rejected}")

            return {**state, "report_data": report_data}

        except Exception as e:
            print(f"[ERROR] Failed to fetch data: {str(e)}")
            return {**state, "errors": [f"Error fetching data: {str(e)}"]}

    async def _generate_summary_node(
        self, state: WeeklyReportState
    ) -> WeeklyReportState:
        """Generate AI summary using LLM"""
        if not state.get("report_data"):
            print("[ERROR] No report data available for summary generation")
            return {
                **state,
                "errors": ["No report data available for summary generation"],
            }

        try:
            report_data = state["report_data"]
            days = state.get("days", 7)

            print(f"[SUMMARY] Generating AI summary for {days} days...")

            # Format entries for LLM
            entries_text = self._format_entries_for_llm(report_data.entries)
            deadlines_text = self._format_deadlines_for_llm(report_data.deadlines)

            # Generate week range
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=days - 1)
            week_range = (
                f"{start_date.strftime('%b %d')} – {end_date.strftime('%b %d')}"
            )

            # Create prompt
            prompt = f"""
            You are a career coach analyzing job application activity for the past week.

            Given the following data from the past {days} days:

            **Statistics:**
            - Total Applications: {report_data.total}
            - Applied: {report_data.applied}
            - Interviews: {report_data.interview}
            - Assessments: {report_data.assessment}
            - Offers: {report_data.offer}
            - Rejections: {report_data.rejected}

            **Recent Applications:**
            {entries_text}

            **Deadlines & Action Items:**
            {deadlines_text}

            **Task:**
            Generate a concise, insightful weekly summary in **5 bullet points** using Markdown format.

            **Include:**
            1. Weekly statistics and highlights (e.g., "Applied to X roles, Y interviews scheduled")
            2. Key updates or notable changes (e.g., "3 rejections but 2 new interviews")
            3. Upcoming deadlines or action items (if any)
            4. Progress assessment (e.g., "Strong week with X% interview conversion")
            5. Recommendations or sentiment (e.g., "Focus on following up with pending applications")

            **Format:**
            Use bullet points with emojis and be encouraging but realistic.
            Keep each point to 1-2 sentences maximum.
            """

            # Generate summary with retry logic
            summary = await self._llm_generate_summary(prompt)

            if summary:
                print("[SUMMARY] Successfully generated AI summary")
                return {**state, "summary": summary, "week_range": week_range}
            else:
                print("[ERROR] Failed to generate summary")
                return {**state, "errors": ["Failed to generate summary"]}

        except Exception as e:
            print(f"[ERROR] Summary generation failed: {str(e)}")
            return {**state, "errors": [f"Summary generation failed: {str(e)}"]}

    async def _llm_generate_summary(self, prompt: str) -> Optional[str]:
        """Generate summary with retry logic"""
        max_retries = 3
        retry_delay = 10

        for attempt in range(max_retries):
            try:
                print(
                    f"[LLM] Generating summary (attempt {attempt + 1}/{max_retries})..."
                )
                result = self.llm.invoke(prompt)
                return result.content.strip()

            except Exception as e:
                if "rate limit" in str(e).lower() or "429" in str(e):
                    if attempt < max_retries - 1:
                        print(
                            f"[RATE LIMIT] Attempt {attempt + 1}/{max_retries} failed. Retrying in {retry_delay}s..."
                        )
                        import asyncio

                        await asyncio.sleep(retry_delay)
                        retry_delay *= 2  # Exponential backoff
                        continue
                    else:
                        print(f"[ERROR] Max retries reached for rate limit: {e}")
                        return None
                else:
                    print(f"[ERROR] LLM call failed: {e}")
                    return None

        return None

    def _format_entries_for_llm(self, entries: List[Dict[str, str]]) -> str:
        """Format entries for LLM processing"""
        if not entries:
            return "No recent applications found."

        entries_text = ""
        for i, entry in enumerate(entries[:10], 1):  # Limit to 10 entries
            entries_text += f"{i}. **{entry.get('company', 'Unknown')}** - {entry.get('job_title', 'Unknown')}\n"
            entries_text += f"   Status: {entry.get('status', 'Applied')} | Applied: {entry.get('applied_on', 'Unknown')}\n"
            if entry.get("notes"):
                entries_text += f"   Notes: {entry.get('notes', '')[:100]}...\n"
            entries_text += "\n"

        return entries_text

    def _format_deadlines_for_llm(self, deadlines: List[Dict[str, str]]) -> str:
        """Format deadlines for LLM processing"""
        if not deadlines:
            return "No upcoming deadlines found."

        deadlines_text = ""
        for i, deadline in enumerate(deadlines, 1):
            deadlines_text += f"{i}. **{deadline.get('company', 'Unknown')}** - {deadline.get('job_title', 'Unknown')}\n"
            deadlines_text += f"   Note: {deadline.get('note', '')[:200]}...\n\n"

        return deadlines_text

    async def _create_report_node(self, state: WeeklyReportState) -> WeeklyReportState:
        """Create weekly report in Notion"""
        from agent.notion_utils import create_weekly_report

        if not state.get("summary") or not state.get("report_data"):
            print("[ERROR] Missing summary or report data")
            return {**state, "errors": ["Missing summary or report data"]}

        try:
            report_data = state["report_data"]
            summary = state["summary"]
            week_range = state.get("week_range", "Unknown")

            print(f"[CREATE] Creating weekly report in Notion...")

            # Generate title
            title = f"Weekly Summary ({week_range})"
            created_on = datetime.now().date().isoformat()

            # Create report in Notion
            result = create_weekly_report(
                title=title,
                week_range=week_range,
                summary=summary,
                created_on=created_on,
            )

            if result:
                print(
                    f"[CREATE] Successfully created weekly report: {result.get('id', 'Unknown')[:8]}..."
                )
                return state
            else:
                print("[ERROR] Failed to create weekly report in Notion")
                return {**state, "errors": ["Failed to create weekly report in Notion"]}

        except Exception as e:
            print(f"[ERROR] Report creation failed: {str(e)}")
            return {**state, "errors": [f"Report creation failed: {str(e)}"]}

    async def run(self, days: int = 7, initial_state: WeeklyReportState = None):
        """Run the weekly report workflow"""
        if initial_state is None:
            initial_state = {
                "days": days,
                "report_data": None,
                "summary": None,
                "week_range": None,
                "errors": [],
            }

        print(f"🚀 Starting Weekly Report workflow for {days} days...")
        result = await self.workflow.ainvoke(initial_state)

        print(f"\n✅ Weekly Report workflow completed!")
        if result.get("report_data"):
            data = result["report_data"]
            print(f"   📊 Total Applications: {data.total}")
            print(
                f"   📝 Summary Generated: {'Yes' if result.get('summary') else 'No'}"
            )
            print(f"   📅 Week Range: {result.get('week_range', 'Unknown')}")

        if result["errors"]:
            print(f"   ❌ Errors: {len(result['errors'])}")
            for error in result["errors"]:
                print(f"      - {error}")

        return result


# Usage
async def main():
    import sys

    # Get days from command line argument
    days = 7
    if len(sys.argv) > 1:
        try:
            days = int(sys.argv[1])
        except ValueError:
            print("Invalid days argument, using default 7 days")

    workflow = WeeklyReportWorkflow()
    result = await workflow.run(days)
    return result


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
