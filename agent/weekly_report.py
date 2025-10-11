import os
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from notion_utils import get_weekly_application_data, create_weekly_report
from llm_utils import invoke_with_retry

load_dotenv()

# === LLM SETUP ===
llm = ChatOpenAI(
    model=os.getenv("OPENROUTER_MODEL"),
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_KEY"),
    temperature=0.3  # Slightly more creative for summaries
)

# === WEEKLY SUMMARY PROMPT ===
summary_prompt = ChatPromptTemplate.from_template("""
You are a career coach analyzing job application activity for the past week.

Given the following data from the past 7 days:

**Statistics:**
- Total Applications: {total}
- Applied: {applied}
- Interviews: {interview}
- Assessments: {assessment}
- Offers: {offer}
- Rejections: {rejected}

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
- Use bullet points (-)
- Be specific with numbers
- Be encouraging but realistic
- Keep it under 300 words total
- Use proper Markdown formatting

**Example output:**
- **Applications Submitted:** 5 new applications this week (Google SDE, Amazon SDE II, Microsoft PM, etc.)
- **Interview Pipeline:** 2 interviews scheduled (Meta - Oct 15, Netflix - Oct 18), maintain momentum by preparing system design topics
- **Assessments Pending:** 1 coding challenge due Oct 20 (Stripe), prioritize completing this before the deadline
- **Conversion Rate:** 40% response rate (2 interviews from 5 applications) - above average, current strategy is working well
- **Action Items:** Follow up on 3 pending applications from last week, prepare for upcoming Meta interview, complete Stripe assessment by Oct 20

Generate the summary:""")

def format_entries_for_llm(entries: list) -> str:
    """Format application entries into readable text for LLM."""
    if not entries:
        return "No applications in the past week."
    
    lines = []
    for i, entry in enumerate(entries, 1):
        status_emoji = {
            "Applied": "📝",
            "Interview": "🎯",
            "Assessment": "💻",
            "Offer": "🎉",
            "Rejected": "❌"
        }.get(entry["status"], "📌")
        
        line = f"{i}. {status_emoji} {entry['company']} - {entry['job_title']} ({entry['status']})"
        if entry.get("applied_on"):
            line += f" - Applied: {entry['applied_on']}"
        if entry.get("notes"):
            # Include first 100 chars of notes
            note_snippet = entry['notes'][:100]
            if len(entry['notes']) > 100:
                note_snippet += "..."
            line += f"\n   Note: {note_snippet}"
        lines.append(line)
    
    return "\n".join(lines)

def format_deadlines_for_llm(deadlines: list) -> str:
    """Format deadline information for LLM."""
    if not deadlines:
        return "No upcoming deadlines detected."
    
    lines = []
    for i, deadline in enumerate(deadlines, 1):
        lines.append(f"{i}. {deadline['company']} - {deadline['job_title']}")
        lines.append(f"   Action: {deadline['note']}")
    
    return "\n".join(lines)

def generate_summary(data: dict) -> str:
    """
    Generate LLM summary from aggregated data.
    
    Args:
        data: Dictionary with application statistics and entries
        
    Returns:
        Markdown-formatted summary string
    """
    print("[LLM] Generating weekly summary...")
    
    # Format data for LLM
    entries_text = format_entries_for_llm(data.get("entries", []))
    deadlines_text = format_deadlines_for_llm(data.get("deadlines", []))
    
    # Generate summary with retry logic
    chain = summary_prompt | llm
    try:
        result = invoke_with_retry(chain, {
            "total": data.get("total", 0),
            "applied": data.get("applied", 0),
            "interview": data.get("interview", 0),
            "assessment": data.get("assessment", 0),
            "offer": data.get("offer", 0),
            "rejected": data.get("rejected", 0),
            "entries_text": entries_text,
            "deadlines_text": deadlines_text
        })
        
        if result is None:
            print("[ERROR] Summary generation failed after retries")
            return "Failed to generate summary. Please try again later."
        
        summary = result.content.strip()
        print("[OK] Summary generated successfully")
        return summary
        
    except Exception as e:
        print(f"[ERROR] Summary generation error: {e}")
        return "Error generating summary. Please check logs."

def get_week_range(days: int = 7) -> tuple:
    """
    Get the date range for the past week.
    
    Returns:
        tuple: (start_date, end_date, formatted_range_string)
    """
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=days - 1)
    
    # Format: "Oct 5 – Oct 12"
    range_str = f"{start_date.strftime('%b %d')} – {end_date.strftime('%b %d')}"
    
    return start_date, end_date, range_str

def generate_weekly_report(days: int = 7):
    """
    Main function to generate and save weekly report.
    
    Args:
        days: Number of days to look back (default: 7)
    """
    print("\n" + "="*70)
    print("📊 WEEKLY JOB APPLICATION REPORT")
    print("="*70 + "\n")
    
    # Step 1: Get week range
    start_date, end_date, week_range = get_week_range(days)
    print(f"[INFO] Generating report for: {week_range}")
    
    # Step 2: Fetch application data
    print(f"[INFO] Fetching applications from Notion (last {days} days)...")
    data = get_weekly_application_data(days)
    
    if data is None:
        print("[ERROR] Failed to fetch application data")
        return False
    
    # Check if there's any data
    if data["total"] == 0:
        print("[INFO] No applications found in the past week. Skipping report generation.")
        return False
    
    # Step 3: Display statistics
    print("\n[STATS] Weekly Statistics:")
    print(f"   Total Applications: {data['total']}")
    print(f"   📝 Applied: {data['applied']}")
    print(f"   🎯 Interviews: {data['interview']}")
    print(f"   💻 Assessments: {data['assessment']}")
    print(f"   🎉 Offers: {data['offer']}")
    print(f"   ❌ Rejections: {data['rejected']}")
    print(f"   ⏰ Deadlines: {len(data['deadlines'])}")
    
    # Step 4: Generate LLM summary
    print("\n[PROCESSING] Generating AI summary...")
    summary = generate_summary(data)
    
    if not summary or summary.startswith("Failed") or summary.startswith("Error"):
        print("[ERROR] Summary generation failed")
        return False
    
    # Step 5: Create report title
    report_title = f"Weekly Summary ({week_range})"
    
    # Step 6: Save to Notion
    print(f"\n[NOTION] Saving report to Notion...")
    result = create_weekly_report(
        title=report_title,
        week_range=week_range,
        summary=summary,
        created_on=end_date.isoformat()
    )
    
    if not result:
        print("[ERROR] Failed to save report to Notion")
        return False
    
    # Step 7: Display summary
    print("\n" + "="*70)
    print("📝 GENERATED SUMMARY:")
    print("="*70)
    print(summary)
    print("="*70)
    
    print(f"\n✅ [SUCCESS] Weekly report generated and saved to Notion!")
    print(f"   Report: {report_title}")
    print(f"   Notion Page ID: {result['id'][:8]}...")
    
    return True

# === CLI INTERFACE ===
if __name__ == "__main__":
    import sys
    
    # Optional: Accept custom day range from command line
    days = 7
    if len(sys.argv) > 1:
        try:
            days = int(sys.argv[1])
            print(f"[INFO] Custom range: {days} days")
        except ValueError:
            print("[WARN] Invalid day argument, using default (7 days)")
    
    success = generate_weekly_report(days)
    sys.exit(0 if success else 1)

