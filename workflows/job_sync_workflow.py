from typing import TypedDict, List, Optional
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from pydantic import BaseModel
import os
import sys
import json
from datetime import datetime
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

load_dotenv()


class EmailData(BaseModel):
    id: str
    subject: str
    sender: str
    date: str
    text: str
    snippet: str


class JobApplicationData(BaseModel):
    company: str
    job_title: str
    status: str
    applied_on: str
    notes: str = ""
    app_id: Optional[str] = None


class JobSyncState(TypedDict):
    emails: List[EmailData]
    processed_emails: List[str]
    applications: List[JobApplicationData]
    errors: List[str]
    current_email: Optional[EmailData]
    current_application: Optional[JobApplicationData]


class JobSyncWorkflow:
    def __init__(self):
        # Initialize LLM with OpenRouter
        self.llm = ChatOpenAI(
            model=os.getenv("OPENROUTER_MODEL", "anthropic/claude-3.5-sonnet"),
            base_url="https://openrouter.ai/api/v1",
            api_key=os.getenv("OPENROUTER_KEY"),
            temperature=0,
        )

        # Create the workflow graph
        self.workflow = self._create_workflow()

    def _create_workflow(self) -> StateGraph:
        workflow = StateGraph(JobSyncState)

        # Add nodes
        workflow.add_node("fetch_emails", self._fetch_emails_node)
        workflow.add_node("process_emails", self._process_emails_node)
        workflow.add_node("create_entries", self._create_entries_node)

        # Set entry point
        workflow.set_entry_point("fetch_emails")

        # Add edges
        workflow.add_edge("fetch_emails", "process_emails")
        workflow.add_edge("process_emails", "create_entries")
        workflow.add_edge("create_entries", END)

        return workflow.compile()

    async def _fetch_emails_node(self, state: JobSyncState) -> JobSyncState:
        """Fetch recent emails from Gmail"""
        from agent.gmail_client import list_messages, get_message, message_summary

        try:
            msg_ids = list_messages(max_results=10, newer_than_days=7)
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

            print(f"[FETCH] Retrieved {len(emails)} emails from Gmail")
            return {**state, "emails": emails}
        except Exception as e:
            print(f"[ERROR] Failed to fetch emails: {str(e)}")
            return {**state, "errors": [f"Error fetching emails: {str(e)}"]}

    def _format_emails_for_llm(self, emails: List[EmailData]) -> str:
        """Format all emails into a single text for LLM processing"""
        emails_text = "=== EMAIL BATCH TO PROCESS ===\n\n"

        for i, email in enumerate(emails, 1):
            emails_text += f"EMAIL {i}:\n"
            emails_text += f"Subject: {email.subject}\n"
            emails_text += f"From: {email.sender}\n"
            emails_text += f"Date: {email.date}\n"
            emails_text += f"Content: {email.text[:2000]}...\n"  # Limit content
            emails_text += f"---\n\n"

        return emails_text

    async def _llm_process_all_emails(
        self, emails_text: str
    ) -> List[JobApplicationData]:
        """Use LLM to process all emails and return deduplicated applications"""

        prompt = f"""
        You are an expert at processing job application emails. You will receive multiple emails and need to extract job applications while avoiding duplicates.

        EMAILS TO PROCESS:
        {emails_text}

        DEDUPLICATION RULES:
        1. Same company = Same application (regardless of job title variations)
        2. Status progression: Applied → Assessment → Interview → Offer → Rejected
        3. Use the most advanced status for the application
        4. Combine notes from all related emails
        5. Use the earliest application date
        6. Preserve Application IDs when available

        EXAMPLES:
        - "Ramp Software Engineer application received" + "Ramp coding assessment" = ONE application with status "Assessment"
        - "Google SDE application" + "Google SDE II interview scheduled" = ONE application with status "Interview"
        - "Amazon rejection" + "Amazon new application" = TWO separate applications (different time periods)

        IMPORTANT:
        - If multiple emails are from the same company, merge them into one application
        - Use the most recent status (e.g., if one email says "Applied" and another says "Assessment", use "Assessment")
        - Combine notes from related emails
        - Use the earliest application date
        - Extract Application IDs when available

        Return ONLY a JSON array of unique applications. Each application should have:
        {{"company", "job_title", "status", "application_date", "notes", "application_id"}}

        Status options: Applied, Assessment, Interview, Offer, Rejected

        Return the JSON array:
        """

        try:
            print("[LLM] Processing emails with deduplication...")
            result = self.llm.invoke(prompt)
            content = result.content.strip()

            # Clean up response (remove markdown if present)
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
                content = content.strip()

            # Parse JSON
            applications_data = json.loads(content)

            # Convert to JobApplicationData objects
            applications = []
            for app_data in applications_data:
                applications.append(
                    JobApplicationData(
                        company=app_data.get("company", ""),
                        job_title=app_data.get("job_title", ""),
                        status=app_data.get("status", "Applied"),
                        applied_on=app_data.get(
                            "application_date", datetime.now().date().isoformat()
                        ),
                        notes=app_data.get("notes", ""),
                        app_id=app_data.get("application_id"),
                    )
                )

            print(f"[LLM] Extracted {len(applications)} unique applications")
            return applications

        except json.JSONDecodeError as e:
            print(f"[ERROR] Failed to parse LLM response as JSON: {e}")
            print(f"[DEBUG] LLM response: {content[:500]}...")
            return []
        except Exception as e:
            print(f"[ERROR] LLM processing failed: {e}")
            return []

    async def _process_emails_node(self, state: JobSyncState) -> JobSyncState:
        """Process all emails in a single LLM call with built-in deduplication"""
        if not state["emails"]:
            print("[PROCESS] No emails to process")
            return state

        print(f"[PROCESS] Processing {len(state['emails'])} emails...")

        # Format all emails for LLM
        emails_text = self._format_emails_for_llm(state["emails"])

        # Single LLM call to process all emails and deduplicate
        consolidated_applications = await self._llm_process_all_emails(emails_text)

        if consolidated_applications:
            print(
                f"[PROCESS] Successfully processed {len(consolidated_applications)} unique applications"
            )
            for app in consolidated_applications:
                print(f"  - {app.company}: {app.job_title} ({app.status})")
        else:
            print("[PROCESS] No applications found in emails")

        return {**state, "applications": consolidated_applications}

    async def _create_entries_node(self, state: JobSyncState) -> JobSyncState:
        """Create entries in Notion (no duplicate checking needed)"""
        from agent.notion_utils import create_or_update_entry

        if not state["applications"]:
            print("[CREATE] No applications to create")
            return state

        print(f"[CREATE] Creating {len(state['applications'])} entries in Notion...")

        for app in state["applications"]:
            try:
                print(
                    f"[CREATE] Processing: {app.company} - {app.job_title} ({app.status})"
                )

                result, was_updated = create_or_update_entry(
                    company=app.company,
                    job_title=app.job_title,
                    status=app.status,
                    applied_on=app.applied_on,
                    notes=app.notes,
                    app_id=app.app_id,
                )

                if result:
                    action = "Updated" if was_updated else "Created"
                    state["processed_emails"].append(
                        f"{action}: {app.company} - {app.job_title}"
                    )
                    print(f"  [OK] {action} entry for {app.company}")
                else:
                    error_msg = f"Failed to create entry for {app.company}"
                    state["errors"].append(error_msg)
                    print(f"  [ERROR] {error_msg}")

            except Exception as e:
                error_msg = f"Error creating entry for {app.company}: {str(e)}"
                state["errors"].append(error_msg)
                print(f"  [ERROR] {error_msg}")

        return state

    async def run(self, initial_state: JobSyncState = None):
        """Run the workflow"""
        if initial_state is None:
            initial_state = {
                "emails": [],
                "processed_emails": [],
                "applications": [],
                "errors": [],
                "current_email": None,
                "current_application": None,
            }

        print("🚀 Starting JobSync workflow...")
        result = await self.workflow.ainvoke(initial_state)

        print(f"\n✅ Workflow completed!")
        print(f"   📧 Emails processed: {len(result['emails'])}")
        print(f"   📝 Applications found: {len(result['applications'])}")
        print(f"   ✅ Entries created: {len(result['processed_emails'])}")

        if result["errors"]:
            print(f"   ❌ Errors: {len(result['errors'])}")
            for error in result["errors"]:
                print(f"      - {error}")

        return result


# Usage
async def main():
    workflow = JobSyncWorkflow()
    result = await workflow.run()
    return result


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
