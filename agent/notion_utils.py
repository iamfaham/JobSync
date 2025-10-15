import os
from notion_client import Client as NotionClient
from dotenv import load_dotenv

load_dotenv()

# === ENVIRONMENT VARIABLES ===
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID")

# === INITIALIZE CLIENT ===
notion = NotionClient(auth=NOTION_TOKEN)


# === CREATE OR UPDATE ENTRY ===
def create_or_update_entry(
    company: str,
    job_title: str,
    status: str,
    applied_on: str,
    notes: str = "",
    app_id: str = None,
):
    """
    Create a new entry or update an existing one if found.

    Args:
        company: Company name
        job_title: Job title
        status: Application status (Applied, Interview, Offer, Rejected, Assessment)
        applied_on: Date in YYYY-MM-DD format
        notes: Additional notes
        app_id: Application ID from email (if available)

    Returns:
        tuple: (page_result, was_updated: bool)
    """
    # Validate inputs
    if not company or not job_title:
        print(
            f"[ERROR] Missing required fields: company='{company}', job_title='{job_title}'"
        )
        return None, False

    # Check if entry already exists by Application ID first
    existing_page = None
    if app_id:
        existing_page = find_entry_by_app_id(app_id)
        if existing_page:
            print(f"[FOUND] Existing entry with Application ID: {app_id}")

    # Fallback: search by company + job title
    if not existing_page:
        existing_page = find_entry_by_company_title(company, job_title)
        if existing_page:
            print(f"[FOUND] Existing entry for {company} - {job_title}")

    # UPDATE existing entry
    if existing_page:
        try:
            old_status = (
                existing_page.get("properties", {})
                .get("Status", {})
                .get("status", {})
                .get("name", "Unknown")
            )
            print(f"[UPDATE] Updating status: {old_status} -> {status}")

            update_props = {
                "Status": {"status": {"name": status}},
            }

            # Add Application ID if provided and not already set
            if app_id:
                update_props["Application ID"] = {
                    "rich_text": [{"text": {"content": app_id}}]
                }

            # Append to notes if new information
            if notes:
                old_notes = (
                    existing_page.get("properties", {})
                    .get("Notes", {})
                    .get("rich_text", [])
                )
                old_notes_text = (
                    old_notes[0].get("text", {}).get("content", "") if old_notes else ""
                )
                if notes not in old_notes_text:
                    new_notes = (
                        f"{old_notes_text}\n\n[Update {applied_on}] {notes}".strip()
                    )
                    update_props["Notes"] = {
                        "rich_text": [{"text": {"content": new_notes}}]
                    }

            result = notion.pages.update(
                page_id=existing_page["id"], properties=update_props
            )

            print(f"   [OK] Updated entry! ID: {result['id'][:8]}...")
            return result, True

        except Exception as e:
            print(f"[ERROR] Update failed: {e}")
            import traceback

            traceback.print_exc()
            return None, False

    # CREATE new entry
    try:
        print(f"[CREATE] Creating new Notion entry...")
        print(f"   Company: {company}")
        print(f"   Job Title: {job_title}")
        print(f"   Status: {status}")
        print(f"   Applied On: {applied_on}")
        if app_id:
            print(f"   Application ID: {app_id}")

        properties = {
            "Title": {"title": [{"text": {"content": f"{company} - {job_title}"}}]},
            "Company": {"rich_text": [{"text": {"content": company}}]},
            "Job Title": {"rich_text": [{"text": {"content": job_title}}]},
            "Status": {"status": {"name": status}},
            "Applied On": {"date": {"start": applied_on}},
            "Notes": {"rich_text": [{"text": {"content": notes or ""}}]},
        }

        # Add Application ID if provided
        if app_id:
            properties["Application ID"] = {
                "rich_text": [{"text": {"content": app_id}}]
            }

        result = notion.pages.create(
            parent={"database_id": NOTION_DATABASE_ID}, properties=properties
        )

        print(f"   [OK] Created in Notion! ID: {result['id'][:8]}...")
        return result, False

    except Exception as e:
        print(f"[ERROR] Notion API call failed: {e}")
        print(f"   Database ID: {NOTION_DATABASE_ID}")
        print(
            f"   Check: 1) Database exists, 2) Integration has access, 3) Properties match"
        )
        import traceback

        traceback.print_exc()
        return None, False


# === FIND EXISTING ENTRY BY APPLICATION ID ===
def find_entry_by_app_id(app_id: str):
    """
    Search for an existing entry by Application ID.
    Returns the page if found, None otherwise.
    """
    if not app_id:
        return None

    try:
        resp = notion.databases.query(
            database_id=NOTION_DATABASE_ID,
            filter={"property": "Application ID", "rich_text": {"equals": app_id}},
        )
        results = resp.get("results", [])
        return results[0] if results else None
    except Exception as e:
        print(f"[WARN] Query by Application ID failed: {e}")
        return None


# === FIND EXISTING ENTRY BY COMPANY + JOB TITLE ===
def find_entry_by_company_title(company: str, job_title: str):
    """
    Search for an existing entry by company and job title.
    Fallback when no Application ID is provided.
    """
    try:
        # Query by company first
        resp = notion.databases.query(
            database_id=NOTION_DATABASE_ID,
            filter={"property": "Company", "rich_text": {"equals": company}},
        )

        # Then filter by job title in results
        for page in resp.get("results", []):
            props = page.get("properties", {})
            page_title = props.get("Job Title", {}).get("rich_text", [])
            if (
                page_title
                and page_title[0].get("text", {}).get("content", "") == job_title
            ):
                return page

        return None
    except Exception as e:
        print(f"[WARN] Query by company/title failed: {e}")
        return None


# === QUERY ENTRIES (used for weekly summary) ===
def query_recent_entries(days: int = 7):
    """
    Fetch entries from the Notion DB created or updated within the last X days.
    """
    import datetime

    cutoff = (
        (datetime.datetime.utcnow() - datetime.timedelta(days=days)).date().isoformat()
    )
    try:
        resp = notion.databases.query(
            **{
                "database_id": NOTION_DATABASE_ID,
                "filter": {
                    "property": "Applied On",
                    "date": {"on_or_after": cutoff},
                },
            }
        )
        return resp.get("results", [])
    except Exception as e:
        print("[WARN] Query failed:", e)
        return []


# === UPDATE ENTRY (optional) ===
def update_entry(page_id: str, status: str):
    """
    Update the status or notes of an existing Notion page.
    """
    try:
        return notion.pages.update(
            page_id=page_id,
            properties={"Status": {"status": {"name": status}}},
        )
    except Exception as e:
        print("[WARN] Update failed:", e)
        return None


# === WEEKLY REPORTS DATABASE ===
NOTION_WEEKLY_REPORTS_DB_ID = os.getenv("NOTION_WEEKLY_REPORTS_DB_ID")


def create_weekly_report(title: str, week_range: str, summary: str, created_on: str):
    """
    Create a new weekly report entry in the Weekly Reports database.

    Args:
        title: Report title (e.g., "Weekly Summary (Oct 5 – Oct 12)")
        week_range: Text field with week range
        summary: LLM-generated markdown summary
        created_on: Date in YYYY-MM-DD format

    Returns:
        Created page object or None on failure
    """
    if not NOTION_WEEKLY_REPORTS_DB_ID:
        print("[ERROR] NOTION_WEEKLY_REPORTS_DB_ID not set in environment")
        return None

    try:
        print(f"[CREATE] Creating weekly report...")
        print(f"   Title: {title}")
        print(f"   Week Range: {week_range}")
        print(f"   Created On: {created_on}")

        properties = {
            "Name": {"title": [{"text": {"content": title}}]},
            "Week Range": {"rich_text": [{"text": {"content": week_range}}]},
            "Summary": {"rich_text": [{"text": {"content": summary}}]},
            "Created On": {"date": {"start": created_on}},
        }

        result = notion.pages.create(
            parent={"database_id": NOTION_WEEKLY_REPORTS_DB_ID}, properties=properties
        )

        print(f"   [OK] Weekly report created! ID: {result['id'][:8]}...")
        return result

    except Exception as e:
        print(f"[ERROR] Failed to create weekly report: {e}")
        import traceback

        traceback.print_exc()
        return None


def get_weekly_application_data(days: int = 7):
    """
    Fetch and aggregate job application data from the last X days.

    Returns:
        dict: Aggregated data with counts, deadlines, and detailed entries
    """
    try:
        entries = query_recent_entries(days)

        # Initialize counters
        data = {
            "total": len(entries),
            "applied": 0,
            "interview": 0,
            "offer": 0,
            "rejected": 0,
            "assessment": 0,
            "deadlines": [],
            "entries": [],
        }

        for entry in entries:
            props = entry.get("properties", {})

            # Extract basic info
            company = props.get("Company", {}).get("rich_text", [])
            company_name = (
                company[0].get("text", {}).get("content", "Unknown")
                if company
                else "Unknown"
            )

            job_title = props.get("Job Title", {}).get("rich_text", [])
            job_title_text = (
                job_title[0].get("text", {}).get("content", "Unknown")
                if job_title
                else "Unknown"
            )

            status_obj = props.get("Status", {}).get("status", {})
            status = status_obj.get("name", "Applied") if status_obj else "Applied"

            applied_on = props.get("Applied On", {}).get("date", {})
            applied_date = applied_on.get("start", "") if applied_on else ""

            notes = props.get("Notes", {}).get("rich_text", [])
            notes_text = notes[0].get("text", {}).get("content", "") if notes else ""

            # Count by status
            status_lower = status.lower()
            if status_lower == "applied":
                data["applied"] += 1
            elif status_lower == "interview":
                data["interview"] += 1
            elif status_lower == "offer":
                data["offer"] += 1
            elif status_lower == "rejected":
                data["rejected"] += 1
            elif status_lower == "assessment":
                data["assessment"] += 1

            # Check for deadlines in notes
            deadline_keywords = [
                "deadline",
                "due",
                "by",
                "before",
                "respond by",
                "complete by",
            ]
            if any(keyword in notes_text.lower() for keyword in deadline_keywords):
                data["deadlines"].append(
                    {
                        "company": company_name,
                        "job_title": job_title_text,
                        "note": notes_text[:200],  # First 200 chars
                    }
                )

            # Store entry details
            data["entries"].append(
                {
                    "company": company_name,
                    "job_title": job_title_text,
                    "status": status,
                    "applied_on": applied_date,
                    "notes": notes_text[:500],  # First 500 chars
                }
            )

        return data

    except Exception as e:
        print(f"[ERROR] Failed to fetch weekly data: {e}")
        import traceback

        traceback.print_exc()
        return None


# === TEST CONNECTION ===
if __name__ == "__main__":
    print("[TEST] Testing Notion connection...")
    try:
        info = notion.databases.retrieve(NOTION_DATABASE_ID)
        print("[OK] Connected to Notion DB:", info["title"][0]["text"]["content"])
    except Exception as e:
        print("[ERROR] Notion test failed:", e)
