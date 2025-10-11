from gmail_connector import get_recent_emails
from notion_utils import create_or_update_entry
from llm_utils import parse_email
from cache_utils import load_cache, save_cache
from datetime import datetime
import json

def daily_sync():
    seen = load_cache()
    emails = get_recent_emails(10)
    new_ids = set(seen)

    for mail in emails:
        mid = mail["id"]
        if mid in seen:
            continue

        print(f"\n[EMAIL] Checking: {mail['subject'][:80]}...")
        
        # Parse email with classification
        parsed = parse_email(
            text=mail["text"],
            subject=mail.get("subject", ""),
            sender=mail.get("from", "")
        )
        
        # Skip if not a real application
        if parsed is None:
            print("   [SKIP] Not a job application")
            new_ids.add(mid)
            continue
        
        # Parse JSON
        try:
            data = json.loads(parsed)
        except json.JSONDecodeError:
            print("   [WARN] Could not parse JSON")
            new_ids.add(mid)
            continue

        # Create or update Notion entry
        status = data.get("status", "Applied")
        app_id = data.get("application_id")
        
        print(f"   [OK] Application found: {data.get('company')} - {data.get('job_title')}")
        print(f"        Status detected: {status}")
        if app_id:
            print(f"        Application ID: {app_id}")
        
        result, was_updated = create_or_update_entry(
            company=data.get("company", ""),
            job_title=data.get("job_title", ""),
            status=status,
            applied_on=data.get("application_date", datetime.now().date().isoformat()),
            notes=data.get("notes", ""),
            app_id=app_id
        )
        
        if not result:
            print(f"   [WARN] Failed to create/update Notion entry (see error above)")

        new_ids.add(mid)

    save_cache(new_ids)
    print("\n[OK] Daily sync complete.")

if __name__ == "__main__":
    daily_sync()
