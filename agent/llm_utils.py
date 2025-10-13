import os
import json
import time
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from dotenv import load_dotenv

load_dotenv()

llm = ChatOpenAI(
    model=os.getenv("OPENROUTER_MODEL"),
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_KEY"),
    temperature=0,
)


# === RETRY WRAPPER FOR RATE LIMITS ===
def invoke_with_retry(chain, params, max_retries=3, delay=10):
    """
    Invoke LLM chain with automatic retry on rate limit errors.

    Args:
        chain: LangChain chain to invoke
        params: Parameters for the chain
        max_retries: Maximum number of retry attempts (default: 3)
        delay: Seconds to wait between retries (default: 10)

    Returns:
        Chain result or None if all retries fail
    """
    for attempt in range(max_retries):
        try:
            return chain.invoke(params)
        except Exception as e:
            error_str = str(e).lower()

            # Check if it's a rate limit error (429)
            is_rate_limit = (
                "429" in error_str
                or "rate limit" in error_str
                or "too many requests" in error_str
                or "rate-limited" in error_str
            )

            if is_rate_limit and attempt < max_retries - 1:
                wait_time = delay * (attempt + 1)  # Incremental backoff
                print(
                    f"[RATE LIMIT] Attempt {attempt + 1}/{max_retries} failed. Retrying in {wait_time}s..."
                )
                time.sleep(wait_time)
            else:
                # Not a rate limit error, or last attempt failed
                raise e

    return None


# Step 1: Classify if this is a real job application
classification_prompt = ChatPromptTemplate.from_template(
    """
Classify if this email is about an ACTUAL job application YOU submitted, or just a job recommendation/alert.

Email subject: {subject}
Email from: {sender}
Email snippet: {text}

Classify as:
- "APPLICATION" - Confirmation you submitted an application, application status update, interview request, offer, rejection
- "NOTIFICATION" - Job recommendations, job alerts, "X is hiring", job board suggestions, newsletters
- "OTHER" - Unrelated emails (GitHub notifications, SSO updates, etc.)

Return ONLY one word: APPLICATION, NOTIFICATION, or OTHER

Examples:
- "Your application to Google has been received" → APPLICATION
- "Amazon application: Status update" → APPLICATION  
- "Interview scheduled with Microsoft" → APPLICATION
- "You might be interested in this Software Engineer role at Meta" → NOTIFICATION
- "LinkedIn: 10 new jobs match your preferences" → NOTIFICATION
- "Indeed: New Machine Learning jobs" → NOTIFICATION
- "GitHub Actions workflow failed" → OTHER
- "Accenture is federating their identity provider" → OTHER

Classification:"""
)

# Step 2: Extract data from real applications
extraction_prompt = ChatPromptTemplate.from_template(
    """
Extract structured information from this job APPLICATION email.

Email:
{text}

Return ONLY valid JSON (no markdown, no explanation) with these exact keys:
{{"company", "job_title", "status", "application_date", "deadline", "notes", "application_id"}}

Rules:
- company: Company name (not the job board like LinkedIn/Indeed/Naukri)
- job_title: Specific job title you applied for
- status: READ THE EMAIL CAREFULLY to determine status. Choose ONE:
  * "Applied" - Initial application confirmation, "we received your application"
  * "Rejected" - Rejection keywords: "unfortunately", "not selected", "not moving forward", 
                 "decided to pursue other candidates", "progress with other candidates",
                 "decided to move forward with other candidates", "position has been filled", 
                 "we regret to inform", "will not be proceeding", "not able to move forward"
  * "Interview" - Interview invitation, "we'd like to schedule", "next round"
  * "Offer" - Job offer, "pleased to offer", "offer letter"
  * "Assessment" - Technical test, coding challenge, assignment requested
- application_date: YYYY-MM-DD format, use today ({today}) if unknown
- deadline: YYYY-MM-DD format or null
- notes: Brief summary (location, salary, key details from the email)
- application_id: Extract the Application ID / Job ID / Reference number from the email if mentioned
  Examples: "ID: 3104541", "Job ID: JOB-2024-001", "Reference: REF-12345", "Application #12345"
  Return null if not found

IMPORTANT: 
1. Carefully read the ENTIRE email to determine the correct status
2. Look for Application ID, Job ID, Reference number, or similar identifiers
3. Return ONLY the JSON object, no markdown code blocks, no explanations
"""
)


def is_job_application(subject: str, sender: str, text: str) -> bool:
    """
    Classify if email is about an actual job application.
    Returns True only for real applications/status updates.
    """
    # Quick filters first (cheap, no LLM call)
    notification_keywords = [
        "job alert",
        "new jobs",
        "job recommendation",
        "might be interested",
        "top matches",
        "jobs match",
        "hiring for",
        "has new",
        "jobs open",
        "be the first to apply",
        "just posted",
        "% match from jobright",
        "jobs like you",
        "job opportunities",
        "recommended for you",
    ]

    other_keywords = [
        "github actions",
        "workflow",
        "run failed",
        "federating",
        "sso",
        "identity provider",
        "newsletter",
        "community update",
    ]

    subject_lower = subject.lower()
    text_lower = text[:500].lower()  # Check first 500 chars

    # Filter out non-job emails FIRST (these are never job applications)
    if any(
        keyword in subject_lower or keyword in text_lower for keyword in other_keywords
    ):
        return False

    # Check for application patterns BEFORE filtering notifications
    # (rejection emails often mention "job opportunities" at the end)
    application_patterns = [
        "application received",
        "application submitted",
        "application status",
        "interview",
        "offer",
        "unfortunately",
        "not moving forward",
        "thank you for applying",
        "your application to",
        "application for",
        "progress with other candidates",
        "pursue other candidates",
        "not selected",
        "position has been filled",
        "we regret",
    ]

    if any(
        pattern in subject_lower or pattern in text_lower
        for pattern in application_patterns
    ):
        return True

    # Now filter out obvious job alert notifications
    # (only if no application keywords were found above)
    if any(
        keyword in subject_lower or keyword in text_lower
        for keyword in notification_keywords
    ):
        return False

    # If unclear, use LLM to classify
    try:
        chain = classification_prompt | llm
        result = invoke_with_retry(
            chain,
            {
                "subject": subject[:200],
                "sender": sender[:100],
                "text": text[:1000],  # First 1000 chars only
            },
        )

        if result is None:
            print(f"[WARN] Classification failed after retries")
            return False

        classification = result.content.strip().upper()
        return classification == "APPLICATION"
    except Exception as e:
        print(f"[WARN] Classification error: {e}")
        return False  # If in doubt, skip it


def parse_email(text: str, subject: str = "", sender: str = ""):
    """
    Parse job application email and extract structured data.

    Args:
        text: Email body text
        subject: Email subject line
        sender: Email sender

    Returns:
        JSON string with job application data, or None if not a real application
    """
    # Step 1: Check if this is a real application
    if not is_job_application(subject, sender, text):
        return None

    # Step 2: Extract data from application
    try:
        from datetime import date

        chain = extraction_prompt | llm
        result = invoke_with_retry(
            chain,
            {
                "text": text[:3000],  # Limit to 3000 chars
                "today": date.today().isoformat(),
            },
        )

        if result is None:
            print(f"[WARN] Extraction failed after retries")
            return None

        # Clean up response (remove markdown if present)
        content = result.content.strip()
        if content.startswith("```"):
            # Remove markdown code blocks
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
            content = content.strip()

        # Validate JSON
        json.loads(content)  # Will raise if invalid
        return content

    except json.JSONDecodeError:
        print(f"[WARN] Could not parse JSON from LLM response")
        return None
    except Exception as e:
        print(f"[WARN] Extraction error: {e}")
        return None
